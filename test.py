import ast

def parse_python_file(file_path, file_content=None):
    """Parse a Python file to extract class and function definitions with their line numbers.
    :param file_path: Path to the Python file.
    :return: Class names, function names, and file contents
    """
    if file_content is None:
        try:
            with open(file_path, "r") as file:
                file_content = file.read()
                parsed_data = ast.parse(file_content)
        except Exception as e:  # Catch all types of exceptions
            print(f"Error in file {file_path}: {e}")
            return [], [], ""
    else:
        try:
            parsed_data = ast.parse(file_content)
        except Exception as e:  # Catch all types of exceptions
            print(f"Error in file {file_path}: {e}")
            return [], [], ""

    class_info = []
    function_names = []
    class_methods = set()

    for node in ast.walk(parsed_data):
        if isinstance(node, ast.ClassDef):
            methods = []
            for n in node.body:
                if isinstance(n, ast.FunctionDef):
                    methods.append(
                        {
                            "name": n.name,
                            "start_line": n.lineno,
                            "end_line": n.end_lineno,
                            "text": file_content.splitlines()[
                                n.lineno - 1 : n.end_lineno
                            ],
                        }
                    )
                    class_methods.add(n.name)
            class_info.append(
                {
                    "name": node.name,
                    "start_line": node.lineno,
                    "end_line": node.end_lineno,
                    "text": file_content.splitlines()[
                        node.lineno - 1 : node.end_lineno
                    ],
                    "methods": methods,
                }
            )
        elif isinstance(node, ast.FunctionDef) and not isinstance(
            node, ast.AsyncFunctionDef
        ):
            if node.name not in class_methods:
                function_names.append(
                    {
                        "name": node.name,
                        "start_line": node.lineno,
                        "end_line": node.end_lineno,
                        "text": file_content.splitlines()[
                            node.lineno - 1 : node.end_lineno
                        ],
                    }
                )

    return class_info, function_names, file_content.splitlines()

def format_parsed_data(class_info, function_names):
    """Format the parsed data into a readable string with headers only.
    
    :param class_info: List of dictionaries with class information.
    :param function_names: List of dictionaries with function information.
    :return: Formatted string representing the classes and functions headers.
    """
    formatted_output = []

    # Format class headers
    for cls in class_info:
        formatted_output.append(f"Class: {cls['name']}")
        if cls['methods']:
            formatted_output.append("  Methods:")
            for method in cls['methods']:
                formatted_output.append(f"    Method: {method['name']}")
        formatted_output.append("")  # Add an empty line for separation

    # Format function headers
    for func in function_names:
        formatted_output.append(f"Function: {func['name']}")
        formatted_output.append("")  # Add an empty line for separation

    return '\n'.join(formatted_output)


class_info, function_names, file_lines = parse_python_file('test_codebase/bias.py')
formatted_output = format_parsed_data(class_info, function_names)
print(formatted_output)

