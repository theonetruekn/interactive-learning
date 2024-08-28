import os
import ast
import json

from os import execv
from pathlib import Path

from SmolCoder.src.meta_tokenizer import Action, MetaToken, MetaTokenizer, Observation
from typing import List 

from typing import List, Optional

from SmolCoder.src.prompting_strategy import PromptingStrategy
from SmolCoder.src.aci import AgentComputerInterface
from SmolCoder.src.llm_wrapper import LLM
from SmolCoder.src.toolkit import Toolkit

from SmolCoder.src.tools.list_codebase_structure import generate_tree, generate_file_list


class SmolCoder:
    """
    This class handles the communication between the prompting strategy and the agent-computer-interface.
    """
    def __init__(self, phase: int, model:LLM, codebase_dir:Path, logger, mode:int = 2) -> None:
        """
        Args:
            mode (int): 0 for github_issue_mode, 1 for repoduce_erro_mode, 2 for ReAct Mode
            phase (int): for testing purposes only, 0 starts with finding sus files, 1 starts with finding sus headers 
        """
        self.model = model
        self.logger = logger
        self.phase = phase
        
        if self.logger is not None:
            self.logger.debug("-------------------------------------------------------------------------------------------")
            self.logger.debug("-------------------------------------------------------------------------------------------")
            self.logger.debug("Started new SmolCoder Run")
            self.logger.debug("SmolCoder initialized with model: %s, codebase_dir: %s, toolkit: %s, prompting_strategy: %s",
                         model, codebase_dir)

    def __call__(self, userprompt: str, number_of_tries: int = 10, start_cwd: str = "") -> str:
        """
        Note that the userprompt needs to start with "[Question]"
        Also note that the __call__ method right now is tailored for ReAct.
        It might need to be adapted for other prompting strategies.
        """
        
        if self.logger is not None:
            self.logger.info("Starting SmolCoder call with userprompt: %s, max_calls: %d", userprompt, max_calls)
            self.logger.info("Starting current working directory: %s", start_cwd)

        # ----------------------------------
        # SYSTEMPROMPT
        # ----------------------------------

        sysprompt = "You will be given a description of a `GitHub issue` and it's corresponding codebase and your task is, to solve this issue. First you will be given a tree structure of the codebase, your task is it based on the description of the issue to select relevant files of it for closer inspection. After this you will be provided with a skeleten for each of your slected file, this skeleton will consist out of class and method headers and your task will be to select the classes and methods that are relevant to the described issue. At the end you will be provided with the source code of your selected classes and methos and asked to fix it.\n"
        sysprompt += "--------------------------------------------\n"
        sysprompt += "You will now be given the description of the GitHub Issue: \n\n"
        sysprompt += userprompt 
        sysprompt += "\n"
        sysprompt += "--------------------------------------------\n"
        
        # ----------------------------------
        # FIND SUS FILES
        # ----------------------------------
        if self.phase == 0:
            print("FIND SUS FILES PHASE:\n\n")
            file_paths = self.find_sus_files(sysprompt, start_cwd, max_files=5, max_tries=5)

        # ----------------------------------
        # FIND SUS CLASSES AND FUNCTIONS
        # ----------------------------------
        if self.phase <= 1:
            if self.phase == 1:
                # Result for df.iloc[0]["problem_statement"]
                file_paths = [
                                "./repos/sqlfluff/src/sqlfluff/core/config.py",
                                "./repos/sqlfluff/src/sqlfluff/core/linter/linted_file.py",
                                "./repos/sqlfluff/src/sqlfluff/core/parser/lexer.py",
                                "./repos/sqlfluff/src/sqlfluff/core/parser/matchable.py",
                              ]

            # max_headers not working yet.
            print("SUS CLASSES AND FUNCTION PHASE:\n\n")
            data = self.find_sus_headers(sysprompt, file_paths, max_headers=5, max_tries=5)
        
        # ----------------------------------
        # FIND SUS CODE SNIPPETS
        # ----------------------------------

        if self.phase <= 2:
            print("SUS CODE SNIPPET PHASE: \n\n")
            if self.phase == 2:
                data = [
                        {
                            "file_path": "./repos/sqlfluff/src/sqlfluff/core/parser/lexer.py",
                            "selected_functions": [
                                "_iter_segments",
                                "_handle_zero_length_slice"
                            ],
                            "selected_classes": [
                                "BlockTracker",
                                "Lexer"
                            ]
                        },
                    ]
            data = self.find_sus_code_snippets(sysprompt, data, max_tries=2)
        
        # ----------------------------------
        #  REPAIR CODE
        # ----------------------------------

        if self.phase <= 3:
            print("REPAIR PHASE:\n\n")
            if self.phase == 3:
                data = [
                        {
                            "file_path": "./repos/sqlfluff/src/sqlfluff/core/parser/lexer.py",
                            "selected_classes": [
                                "BlockTracker",
                                "Lexer"
                            ]
                        },
                    ]
            self.repair(sysprompt, data)
    
    def parse_python_file(self, file_path, file_content=None):
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

    def format_parsed_data(self, class_info, function_names):
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

    def parse_json_string(self, json_string):
        """
        Returns:
            Valid: True when json is vlaid otherwise false
            data: Either the json data, or an error code
        """
        try:
            # Remove the '--- END OF LIST ---' if it's present
            if '--- END OF LIST ---' in json_string:
                json_string = json_string.replace('--- END OF LIST ---', '').strip()
            
            # Attempt to parse the JSON string into a Python object
            data = json.loads(json_string)
            
            # Check if the top-level structure is a list
            if not isinstance(data, list):
                return (False, "Error: JSON should start with a list of dictionaries.")
            
            for i, item in enumerate(data):
                if not isinstance(item, dict):
                    return (False, f"Error: Element at index {i} should be a dictionary.")
                
                # Check for the 'file_path' key and its type
                if 'file_path' not in item:
                    return (False, f"Error: Missing 'file_path' key in element at index {i}.")
                if not isinstance(item['file_path'], str):
                    return (False, f"Error: 'file_path' at index {i} should be a string.")
                
                # Check for 'selected_functions' and 'selected_classes' keys and their types
                if 'selected_functions' not in item or not isinstance(item['selected_functions'], list):
                    return (False, f"Error: 'selected_functions' at index {i} should be a list.")
                if 'selected_classes' not in item or not isinstance(item['selected_classes'], list):
                    return (False, f"Error: 'selected_classes' at index {i} should be a list.")
                
                # Convert all elements in 'selected_functions' and 'selected_classes' to strings
                item['selected_functions'] = [str(func) for func in item['selected_functions']]
                item['selected_classes'] = [str(cls) for cls in item['selected_classes']]
            
            return (True, data)
        
        except json.JSONDecodeError as e:
            return (False, f"Error: Failed to parse JSON. {str(e)}")
    
    def validate_json_classes_functions(self, data):
        """
            Return:
                Valid: True when no error was found otherwise false
                Error_string: contains a string describing all errors
                filtered_data: only contains data which is correct
            """
        def get_definitions(file_content):
            """Parse the Python file and return a dictionary with the classes and functions found."""
            tree = ast.parse(file_content)
            definitions = {"classes": set(), "functions": set()}

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    definitions["classes"].add(node.name)
                elif isinstance(node, ast.FunctionDef):
                    definitions["functions"].add(node.name)

            return definitions

        valid = True
        error_messages = []
        filtered_data = []

        for item in data:
            file_path = item["file_path"]
            selected_functions = set(item["selected_functions"])
            selected_classes = set(item["selected_classes"])

            if not os.path.exists(file_path):
                valid = False
                error_messages.append(f"File not found: {file_path}")
                continue  # Skip to the next item, do not add this file to filtered_data

            try:
                with open(file_path, 'r') as file:
                    file_content = file.read()

                definitions = get_definitions(file_content)
                
                missing_functions = selected_functions - definitions["functions"]
                missing_classes = selected_classes - definitions["classes"]

                # Filter out missing functions and classes
                valid_functions = selected_functions - missing_functions
                valid_classes = selected_classes - missing_classes

                if missing_functions:
                    valid = False
                    error_messages.append(
                        f"Missing functions in {file_path}: {', '.join(missing_functions)}"
                    )
                if missing_classes:
                    valid = False
                    error_messages.append(
                        f"Missing classes in {file_path}: {', '.join(missing_classes)}"
                    )

                if valid_functions or valid_classes:
                    filtered_data.append({
                        "file_path": file_path,
                        "selected_functions": list(valid_functions),
                        "selected_classes": list(valid_classes)
                    })

            except Exception as e:
                valid = False
                error_messages.append(f"Error processing {file_path}: {str(e)}")

        return valid, "\n".join(error_messages), filtered_data
   
    def prompt_list_files(self, n=5):
        return (
            "Please provide the list of file paths in plain text format, without any whitespaces. "
            "Each file path should be on a new line and without any whitespaces. "
            "At the end of the list, include the specific stop token `--- END OF LIST ---` to indicate "
            "the end of the list.\n\n"
            f"Please only provide the full path and return at most {n} files. Do not provide commentary.\n"
            "The returned files should be separated by new lines.\n"
            "DO NOT ADD ANYTHING ELSE TO YOUR RESPONSE.\n\n"
            "For example:\n"
            "/documents/report.py\n"
            "/pictures/vacation.py\n"
            "/music/song.py\n"
            "--- END OF LIST ---\n\n"
            "To repeat:\n"
            "- Each file path should be listed on its own line.\n"
            "- After the last file path, include the stop token `--- END OF LIST ---` on a new line. "
            "This token indicates the end of the file paths list.\n"
            "- There should be no additional formatting or characters besides the file paths and the stop token.\n"
            "- DO NOT USE WHITESPACE\n"
            "Your file list:\n"
        )

    def find_sus_files(self, sysprompt, start_cwd, max_tries=5, max_files=5) -> List[str]:
        trajectory = ""
        trajectory += sysprompt
        trajectory += "You will now be given the structure of codebase corresponding to the Issue:\n"
        trajectory += "```\n"
        trajectory += generate_file_list(start_cwd)
        trajectory += "\n"
        trajectory += "```\n"
        trajectory += "--------------------------------------------\n"
        trajectory += "Now that you have seen structure of the codebase please select files that you think are relevenat to the issue. "
        
        trajectory += self.prompt_list_files(n=max_files)

        # We give the LLM multiple tries to correctly output a list of files
        file_paths = []
        found_paths = False
        for _ in range(max_tries):
            
            llm_response = self.model.query_completion(trajectory, stop_token="--- END OF LIST ---")
            trajectory += llm_response
            print(trajectory)
            trajectory += "\n"
            trajectory += "--------------------------------------------\n"

            # Parse the llm response to see if the output is correctly structured
            llm_file_paths, error = self.parse_file_paths(llm_response, start_cwd)
            
            if error:
                trajectory += "While parsing your provided list of selected file paths an error was found: \n"
                trajectory += error
                trajectory += "\n"
                trajectory += "--------------------------------------------\n"
                trajectory += "Please try again."
                trajectory += self.prompt_list_files(max_files - len(file_paths))
                continue

            # Check if the files exist and are python files
            errors = self.check_file_paths(llm_file_paths)

            # append the valid file paths that have not already been appended to the main list
            valid_paths = [path for path in llm_file_paths if path not in errors and path not in file_paths]
            file_paths.extend(valid_paths)


            # If there are errors, report them to the LLM and continue the loop
            if errors:
                trajectory += "While parsing your provided list of selected file paths, the following errors were found:\n"
                for path, error_msg in errors.items():
                    trajectory += f'{path}: {error_msg}\n'
                
                trajectory += "--------------------------------------------\n"
                trajectory += "Please try again."
                trajectory += self.prompt_list_files(max_files - len(file_paths))
                continue

            if len(file_paths) == 5:
                break
        
        print(trajectory)
        print("------------------------------------\n")
        
        if not file_paths:
            print("Sucks to suck, LLM didn't find any paths.")
        else:
            print(f"Found the following paths: ", str(file_paths))

        return file_paths
    
    def prompt_list_headers(self, max_headers=5):
        return (
                "Please provide a list of classes or functions in JSON file format. "
                "Use an array, where each entry has the following elements: `file_path`, "
                "`selected_functions`, and `selected_classes`. The `file_path` should point to the file "
                "containing the `selected_functions` and `selected_classes`, which are arrays. "
                            f"Please only provide the full path and return at most {max_headers} files. Do not provide commentary.\n"
                "End your output with the stop token `--- END OF LIST ---`.\n\n"
                "DO NOT ADD ANYTHING ELSE TO YOUR RESPONSE.\n\n"
                "**Example Output:**\n"
            "[\n"
            "    {\n"
            '        "file_path": "/torch/nn/attention/bias.py",\n'
            '        "selected_functions": ["causal_upper_left", "causal_upper_right"],\n'
            '        "selected_classes": ["CausalVariant", "CausalBias"]\n'
            "    },\n"
            "    {\n"
                '        "file_path": "/torch/fx/passes/reinplace.py",\n'
                '        "selected_functions": [],\n'
                '        "selected_classes": ["_ViewType"]\n'
                "    }\n"
                "]\n"
                "--- END OF LIST ---\n\n"
                
                "Your class and function list:\n"
            )

    def find_sus_headers(self, sysprompt, file_paths, max_headers, max_tries):
        # We now want to ask the LLM for suspicious classes 
        # For that we reset the context, because our context is limited
        trajectory = ""
        trajectory += sysprompt
        trajectory += "In a previous iteration you've already found files that might be relevant to the described Issue. We now want to look closer and identify classes and functions that are relevant to the described Issue. For this purpose you will receive a list of classes and function and you should choose ones that are relevant to the described issue.\n"
        trajectory += "--------------------------------------------\n"
        trajectory += "You will now be given the headers of classes and function:\n"
    
        # Create the headers string
        file_skeletons = ""
        for path in file_paths:
            class_info, function_names, file_lines = self.parse_python_file(path)
            formatted_output = self.format_parsed_data(class_info, function_names)
                
            file_skeletons += f"Headers for {path}\n"
            file_skeletons += "```\n"
            file_skeletons += formatted_output
            file_skeletons += "```\n"

        trajectory += file_skeletons
        trajectory += "--------------------------------------------\n"
        trajectory += "Now that you have seen, all the classes and function of the relevant files please select classes and function that you think are relevant to the issue. \n"
        trajectory += self.prompt_list_headers(max_headers)
        data = None
        found_headers = False
        filtered_data = None
        for _ in range(max_tries):
            # Query the LLM for its choice of classes/functions.
            llm_response = self.model.query_completion(trajectory, stop_token="--- END OF LIST ---")
            
            # Add the reponse of the llm to our trajectory
            trajectory += llm_response
            trajectory += "\n"
            trajectory += "--------------------------------------------\n"

            # This only checks if its valid json code
            status, data = self.parse_json_string(llm_response)
            if not status:
                trajectory += "While parsing your provided a list of selected classes and functions an error was found: \n"
                trajectory += data
                trajectory += "\n"
                trajectory += "--------------------------------------------\n"
                trajectory += "Please try again."
                trajectory += self.prompt_list_headers(max_headers)
                continue
            
            # This checks if the functions and classes inside the json exist
            valid, error, filtered_data = self.validate_json_classes_functions(data)
            if not valid:
                trajectory += "While parsing your provided a list of selected classes and functions an error was found: \n"
                trajectory += error
                trajectory += "\n"
                trajectory += "--------------------------------------------\n"
                trajectory += "Please try again."
                trajectory += self.prompt_list_headers(max_headers)
                continue

            # If we didn't find any error we can go out of the loop
            found_headers = True
            break
        
        print(trajectory)
        print("------------------------------------\n")
        print("------------------------------------\n")
        
        if not found_headers:
            print("Sucks to suck, LLM didn't find only valid classes/functions.")
            return filtered_data
        else:
            print("found the following data: ", str(data))
            return data

    def parse_file_paths(self, text, start_cwd, stop_token='--- END OF LIST ---'):
        """
        Parses a list of file paths from the given plain text.

        Args:
            text (str): The plain text input containing file paths and the stop token.
            stop_token (str): The token indicating the end of the list. Default is '--- END OF LIST ---'.

        Returns:
            tuple: A tuple containing a list of file paths and an error message (if any).
        """
        if not isinstance(text, str):
            return [], 'Error: Input is not a valid string.'

        if not isinstance(stop_token, str) or not stop_token:
            return [], 'Error: Stop token must be a non-empty string.'

        # Split the text into lines and initialize variables
        lines = text.strip().split('\n')
        file_paths = []
        
        if not lines:
            return [], 'Error: The input is empty or only contains whitespace.'

        stop_token_found = False

        for line in lines:
            line = line.strip()
            if not line:
                continue  # Skip empty lines
            
            if line == stop_token:
                stop_token_found = True
                break
            
            # Construct the full file path and check if it exists
            full_path = os.path.join(start_cwd, line)
            file_paths.append(full_path)

        # Check if the stop token was found
        if not stop_token_found:
            return [], f'Error: Missing stop token `{stop_token}`.'

        # If there are lines after the stop token, return an error
        remaining_lines = lines[lines.index(stop_token) + 1:]
        if any(line.strip() for line in remaining_lines):
            return [], f'Error: Content found after the stop token `{stop_token}`.'

        return file_paths, None

    def check_file_paths(self, file_paths):
        """
        Checks if all file paths in the given list are valid Python files (i.e., they exist on the filesystem and have a .py extension).

        Args:
            file_paths (list): A list of file paths to check.

        Returns:
            dict: A dictionary where keys are invalid file paths and values are error messages. 
                Only paths with errors are included.
        """
        errors = {}

        for path in file_paths:
            path = path.strip()
            if not path:
                errors[path] = 'Error: Path is empty or whitespace.'
                continue

            if not os.path.isfile(path):
                errors[path] = 'Error: File does not exist.'
                continue

            if not path.lower().endswith('.py'):
                errors[path] = 'Error: File is not a Python file (does not have a .py extension).'
                continue

        return errors

    def find_sus_code_snippets(self, sysprompt, data, max_tries=5):
        relevant_data = []

        # Iterate through each element in the JSON data
        for element in data:
            file_path = element.get("file_path")
            selected_functions = element.get("selected_functions", [])
            selected_classes = element.get("selected_classes", [])
            
            relevant_functions = []
            relevant_classes = []

            # Process each function in the selected_functions list
            for func in selected_functions:
                # Extract the code snippet for the current function
                code_string = self.extract_code_snippets(file_path, func_name=func, class_name=None)
                
                # Handle extraction errors
                if code_string.startswith("Error"):
                    print(f"Error while extracting code for function '{func}' in file '{file_path}'")
                    continue

                # Determine relevance using the LLM
                response = self.evaluate_relevance(sysprompt, code_string, max_tries)
                if response == "YES.":
                    relevant_functions.append(func)

            # Process each class in the selected_classes list
            for cls in selected_classes:
                # Extract the code snippet for the current class
                code_string = self.extract_code_snippets(file_path, func_name=None, class_name=cls)
                
                if code_string.startswith("Error"):
                    print(f"Error while extracting code for class '{cls}' in file '{file_path}'")
                    continue

                # Determine relevance using the LLM
                response = self.evaluate_relevance(sysprompt, code_string, max_tries)
                if response == "YES.":
                    relevant_classes.append(cls)

            # Add the relevant functions and classes to the output if any exist
            if relevant_functions or relevant_classes:
                relevant_data.append({
                    "file_path": file_path,
                    "selected_functions": relevant_functions,
                    "selected_classes": relevant_classes
                })

        if not relevant_data:
            print("No relevant classes/functions were found.")
        else:
            print("Relevant classes/functions identified: ", relevant_data)

        # Return the relevant data in JSON format
        return relevant_data

    def evaluate_relevance(self, sysprompt, code_string, max_tries=5):
        trajectory = (
            f"{sysprompt}"
            "We now want to identify whether the following code snippet is relevant to the described issue.\n"
            "You will be provided with a source code snippet. You should decide whether it is relevant to the issue.\n"
            "Please respond with either 'YES.' or 'NO.'.\n"
            "Example Answer:\n"
            "YES."
            "--------------------------------------------\n"
            "Here is the code snippet:\n"
            f"{code_string}\n"
            "--------------------------------------------\n"
            "Is this code snippet relevant to the issue? Please respond with 'YES.' or 'NO.'.\n"
        )
        print(trajectory)
        
        for _ in range(max_tries):
            llm_response = self.model.query_completion(trajectory, stop_token=".")
            print(llm_response)
            
            response = llm_response.strip().upper()
            if response in ["YES.", "NO."]:
                return response
            else:
                # If the response is invalid, adjust the prompt to clarify the requirement
                trajectory += "\nYour response was invalid. Please respond with either 'YES.' or 'NO.' only."

        print("Failed to obtain a valid response from the LLM.")
        return "NO."
        
    def extract_code_snippets(self, file_path, func_name=None, class_name=None):
        try:
            with open(file_path, 'r') as file:
                source_code = file.read()
        except FileNotFoundError:
            return f"Error: File not found at path {file_path}"
        except Exception as e:
            return f"Error: Unable to read file {file_path} due to {str(e)}"
        
        # Parse the source code into an AST
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return f"Error: Failed to parse Python source file due to syntax error: {str(e)}"
        
        # Extract the function or class node
        target_node = None
        if func_name:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    target_node = node
                    break
        elif class_name:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    target_node = node
                    break
        
        # If the target node wasn't found, return an error
        if target_node is None:
            target_type = "function" if func_name else "class"
            return f"Error: {target_type} '{func_name or class_name}' not found in file {file_path}"

        # Get the lines of the target node
        start_line = target_node.lineno - 1  # Line numbers in AST are 1-based
        end_line = target_node.end_lineno if hasattr(target_node, 'end_lineno') else None

        # Return the relevant lines of code
        code_lines = source_code.splitlines()
        extracted_code = "\n".join(code_lines[start_line:end_line])

        return extracted_code

    def repair(self, sysprompt, data):
        # Iterate through each element in the JSON data
        for element in data:
            file_path = element.get("file_path")
            selected_functions = element.get("selected_functions", [])
            selected_classes = element.get("selected_classes", [])
            
            relevant_functions = []
            relevant_classes = []

            # Process each function in the selected_functions list
            for func in selected_functions:
                # Extract the code snippet for the current function
                code_string = self.extract_code_snippets(file_path, func_name=func, class_name=None)
                
                # Handle extraction errors
                if code_string.startswith("Error"):
                    print(f"Error while extracting code for function '{func}' in file '{file_path}'")
                    continue

                self.generate_patch(sysprompt, code_string)

            # Process each class in the selected_classes list
            for cls in selected_classes:
                # Extract the code snippet for the current class
                code_string = self.extract_code_snippets(file_path, func_name=None, class_name=cls)
                
                if code_string.startswith("Error"):
                    print(f"Error while extracting code for class '{cls}' in file '{file_path}'")
                    continue

                self.generate_patch(sysprompt, code_string)
    
    def generate_patch(self, sysprompt, code_string, max_tries=5):
        # Construct the prompt for the LLM to generate the patch
        prompt = (
            f"{sysprompt}"
            "We want to generate a patch for the following code snippet based on the described issue.\n"
            "You will be provided with a source code snippet, and you should generate a patch to fix the issue described earlier.\n"
            "The patch should be in the standard unified diff format.\n"
            "--------------------------------------------\n"
            "Here is the code snippet:\n"
            f"{code_string}\n"
            "--------------------------------------------\n"
            "Please provide the patch in the unified diff format below:\n"
        )
        
        for _ in range(max_tries):
            # Query the LLM to generate a patch
            llm_response = self.model.query_completion(prompt, stop_token=None)
            print(llm_response)

            # Verify if the response is a valid patch
            if self.is_valid_patch(llm_response):
                # Save the patch to a file
                self.save_patch_to_file(llm_response)
                return

            # If invalid, adjust the prompt to clarify the format requirement
            prompt += "\nYour response was not a valid patch. Please provide a valid patch in unified diff format."

        print("Failed to obtain a valid patch from the LLM.")

    def is_valid_patch(self, patch_string):
        # Basic validation to check if the patch string contains diff format headers
        return patch_string.startswith("diff") or patch_string.startswith("---")

    def save_patch_to_file(self, patch_string):
        patch_dir = "patches"
        if not os.path.exists(patch_dir):
            os.makedirs(patch_dir)
        
        patch_filename = os.path.join(patch_dir, "patch.diff")

        with open(patch_filename, "w") as patch_file:
            patch_file.write(patch_string)
        
        print(f"Patch saved to {patch_filename}.")
