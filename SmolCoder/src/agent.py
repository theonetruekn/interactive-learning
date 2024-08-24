import os
import ast

from os import execv
from pathlib import Path

from SmolCoder.src.meta_tokenizer import Action, MetaToken, MetaTokenizer, Observation
from typing import List 

from typing import List, Optional

from SmolCoder.src.prompting_strategy import PromptingStrategy
from SmolCoder.src.aci import AgentComputerInterface
from SmolCoder.src.llm_wrapper import LLM
from SmolCoder.src.toolkit import Toolkit

from SmolCoder.src.tools.list_codebase_structure import generate_tree


class SmolCoder:
    """
    This class handles the communication between the prompting strategy and the agent-computer-interface.
    """
    def __init__(self, model:LLM, codebase_dir:Path, toolkit:Toolkit, logger, prompting_strategy:str = "ReAct", mode:int = 2) -> None:
        if prompting_strategy != "ReAct":
            raise NotImplementedError("Currently, only 'ReAct' is a valid answer.")
        
        """
        Args:
            mode (int): 0 for github_issue_mode, 1 for repoduce_erro_mode, 2 for ReAct Mode
        """
        self.model = model
        self.logger = logger
        self.ACI = AgentComputerInterface(cwd=codebase_dir, tools=toolkit, logger=self.logger)
        self.prompting_strategy = PromptingStrategy.create(model, 
                                                           strategy=prompting_strategy, 
                                                           toolkit=toolkit, 
                                                           mode=mode
                                                           )
        self.meta_tokenizer = MetaTokenizer(toolkit)
        self.token_stream: List[MetaToken] = [] # this saves the tokens (Action, Thought, Observation, ...)
        self._history = [] # this saves the history of the trajectory
        
        if self.logger is not None:
            self.logger.debug("-------------------------------------------------------------------------------------------")
            self.logger.debug("-------------------------------------------------------------------------------------------")
            self.logger.debug("Started new SmolCoder Run")
            self.logger.debug("SmolCoder initialized with model: %s, codebase_dir: %s, toolkit: %s, prompting_strategy: %s",
                         model, codebase_dir, toolkit, prompting_strategy)
    
    def inspect_history(self, n:Optional[int] = None) -> str:
        if not n:
            return self._format_history(self._history)
        else:
            return self._format_history(self._history[-n:])
    
    def _format_history(self, history_input: List[str]) -> str:
        result = ""
        for item in history_input:
            result += item 

        return result 

    def _backtrack_action(self) -> bool:
        if isinstance(self.token_stream[-1], Action):
            self.token_stream.pop()
            return True
        return False

    def __call__(self, userprompt: str, max_calls: int = 10, start_cwd: str = "") -> str:
        """
        Note that the userprompt needs to start with "[Question]"
        Also note that the __call__ method right now is tailored for ReAct.
        It might need to be adapted for other prompting strategies.
        """
        if start_cwd != "":
            self.ACI._change_cwd(start_cwd)
        
        if self.logger is not None:
            self.logger.info("Starting SmolCoder call with userprompt: %s, max_calls: %d", userprompt, max_calls)
            self.logger.info("Starting current working directory: %s", start_cwd)
        
        sysprompt = "You will be given a description of a `GitHub issue` and it's corresponding codebase and your task is, to solve this issue. First you will be given a tree structure of the codebase, your task is it based on the description of the issue to select relevant files of it for closer inspection. After this you will be provided with a skeleten for each of your slected file, this skeleton will consist out of class and method headers and your task will be to select the classes and methods that are relevant to the described issue. At the end you will be provided with the source code of your selected classes and methos and asked to fix it.\n"
        sysprompt += "--------------------------------------------\n"
        sysprompt += "You will now be given the description of the GitHub Issue: \n\n"
        sysprompt += userprompt 
        sysprompt += "\n"
        sysprompt += "--------------------------------------------\n"
                
        trajectory = ""
        trajectory += sysprompt
        trajectory += "You will now be given the structure of codebase corresponding to the Issue:\n"
        trajectory += "```\n"
        trajectory += generate_tree(start_cwd)
        trajectory += "\n"
        trajectory += "```\n"
        trajectory += "--------------------------------------------\n"
        trajectory += "Now that you have seen structure of the codebase please select files that you think are relevenat to the issue. "
        prompt_list_files = """
Please provide the list of file paths in plain text format, without any whitespaces. Each file path should be on a new line and without any whitespaces. At the end of the list, include the specific stop token `--- END OF LIST ---` to indicate the end of the list.

**Example Output:**
/documents/report.py
/pictures/vacation.py
/music/song.py
--- END OF LIST ---

**Explanation:**
- Each file path should be listed on its own line.
- After the last file path, include the stop token `--- END OF LIST ---` on a new line. This token indicates the end of the file paths list.
- There should be no additional formatting or characters besides the file paths and the stop token. \n
Your file list: \n
        """
        trajectory += prompt_list_files

        # We give the LLM multiple tries to correctly output a list of files
        file_paths = [] 
        for _ in range(5):
            # Query the LLM for its choice of files.
            llm_response = self.model.query_completion(trajectory, stop_token="--- END OF LIST ---")
            
            # Add the reposne of the llm to our trajectory
            trajectory += llm_response
            trajectory += "\n"
            trajectory += "--------------------------------------------\n"


            # Parse the list out of the llm response and check for errors
            file_paths, error = self.parse_file_paths(llm_response)
            
            if error:
                trajectory += "While parsing your provided a list of selected file paths an error was found: \n"
                trajectory += error
                trajectory += "\n"
                trajectory += "--------------------------------------------\n"
                trajectory += "Please try again."
                trajectory += prompt_list_files
                continue
        
            # Check if there are any errors
            validity = self.check_file_paths(file_paths)
            errors_found = any(status != 'Valid' for status in validity.values())
            
            if errors_found:
                trajectory += "While parsing your provided a list of selected file paths an error was found: \n"
                for path, status in validity.items():
                    trajectory += f'{path}: {status}\n'
                
                trajectory += "--------------------------------------------\n"
                trajectory += "Please try again."
                trajectory += prompt_list_files
                continue
        
        print(trajectory)
        print("------------------------------------")
        print("------------------------------------")

        # We now want to ask the LLM for suspicious classes 
        # For that we reset the context, because our context is limited
        trajectory = ""
        trajectory += sysprompt
        trajectory += "In a previous iteration you've already found files that might be relevant to the described Issue. We now want to look closer and identify classes and functions that are relevant to the described Issue. For this purpose you will receive a list of classes and function and you should choose ones that are relevant to the described issue.\n"
        trajectory += "--------------------------------------------\n"
        trajectory += "You will now be given the headers of classes and function:\n"
        
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
        trajectory += "Now that you have seen, all the classes and function of the relveant files please select classes and function that you think are relevant to the issue. \n"
        prompt_headers = """
Please provide a list of classes or functions in json file format. Use an array, where each entry has the following elements: `file_path`, `selected_functions` and `selected_classes`, where `file_path` point towards the file within which are the `selected_functions` and `selected_classes` which are arrays.

**Example Output:**
[
    {
        "file_path": "/torch/nn/attention/bias.py",
        "selected_functions": [causal_upper_left, causal_upper_right],
        "selected_classes": [CausalVariant, CausalBias],
    },
    {
        "file_path": "/torch/fx/passes/reinplace.py",
        "selected_functions": [],
        "selected_classes": [_ViewType],
    },
]

Your class and function list: \n
"""
        trajectory += prompt_headers

        return trajectory




    def parse_file_paths(self, text, stop_token='--- END OF LIST ---'):
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
            
            if not line:
                return [], 'Error: Found an empty line in the file paths list.'

            file_paths.append(line)

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
            dict: A dictionary where keys are file paths and values are error messages or 'Valid' if the file is a valid Python file.
        """
        validity = {}

        for path in file_paths:
            path = path.strip()
            if not path:
                validity[path] = 'Error: Path is empty or whitespace.'
                continue
            
            if not os.path.isfile(path):
                validity[path] = 'Error: File does not exist.'
                continue
            
            if not path.lower().endswith('.py'):
                validity[path] = 'Error: File is not a Python file (does not have a .py extension).'
                continue
            
            validity[path] = 'Valid'

        return validity
    
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



