import os
import ast 

from pathlib import Path
from typing import List


from SmolCoder.src.tools.tool import Tool

class ListMethods(Tool):    
    @property
    def name(self) -> str:
        return "List_Methods"
    
    @property
    def input_variables(self) -> List[str]:
        return ["class_name"]

    @property
    def desc(self) -> str:
        return "lists the signatures and docstring of all the method of the class `class_name`."
   
    @property 
    def example(self):
        return f'{self.name}[MyClass]'

    def __call__(self, input_variables:List[str], cwd:Path, logger) -> str:
        """
        Extracts function signatures and docstrings from the specified class 
        found in Python files within the provided directory.

        Parameters:
        cwd (str): The current working directory to search for Python files.
        class_name (str): The name of the class to extract information from.

        Returns:
        dict: A dictionary where keys are function names and values are tuples 
        containing function signature and docstring.
        """
        class_name = input_variables[0]
        class FunctionVisitor(ast.NodeVisitor):
            def __init__(self):
                self.functions = {}

            def visit_FunctionDef(self, node):
                if isinstance(node, ast.FunctionDef):
                    # Get function name
                    func_name = node.name

                    # Get function signature
                    args = [arg.arg for arg in node.args.args]
                    signature = f"{func_name}({', '.join(args)})"

                    # Get function docstring
                    docstring = ast.get_docstring(node)

                    # Store in dictionary
                    self.functions[func_name] = (signature, docstring)
                
                self.generic_visit(node)

        class ClassVisitor(ast.NodeVisitor):
            def __init__(self, target_class_name):
                self.target_class_name = target_class_name
                self.function_visitor = FunctionVisitor()
                self.inside_target_class = False

            def visit_ClassDef(self, node):
                if node.name == self.target_class_name:
                    self.inside_target_class = True
                    self.function_visitor.visit(node)
                    self.inside_target_class = False
                else:
                    self.generic_visit(node)

        def parse_file(file_path):
            with open(file_path, "r") as source_file:
                source_code = source_file.read()

            # Parse the source code into an AST
            tree = ast.parse(source_code)

            # Initialize and run the class visitor
            class_visitor = ClassVisitor(class_name)
            class_visitor.visit(tree)

            return class_visitor.function_visitor.functions

        all_functions = {}

        # Walk through the directory and process each Python file
        for root, _, files in os.walk(cwd):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    functions_info = parse_file(file_path)
                    all_functions.update(functions_info)
        
        if not bool(all_functions):
            return "In the current working directory does not exist a class named: " + str(class_name)
        else:
            output = []
            for method_name, (signature, docstring) in all_functions.items():
                output.append(f"Method {signature} with docstring {{ {docstring} }}")
            return ', '.join(output) 

    def _indent(self, text, spaces):
        indent = ' ' * spaces
        return '\n'.join(indent + line if line.strip() else line for line in text.split('\n'))
