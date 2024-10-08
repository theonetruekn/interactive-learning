import ast
from pathlib import Path
from typing import List
import os 

from SmolCoder.src.tools.tool import Tool

class ListClasses(Tool):
    @property
    def name(self) -> str:
        return "List_Classes"

    @property
    def input_variables(self) -> List[str]:
        return ["file_name"]

    @property
    def desc(self) -> str:
        return f"lists all class names and their docstring that are in the Python file {self.input_variables[0]}."
    
    @property 
    def example(self):
        return f"{self.name}[test.py]"

    def __call__(self, input_variables: List[str], cwd: Path, logger) -> str:
        file_name = input_variables[0]
        
        file_path = cwd / file_name
        
        if logger:
            logger.debug("ListClasses in the file %s", file_path) 
       
        if not file_path.exists():
            return f'The specified file does not exist: {file_path}'
        
        if os.path.isdir(file_path):
            return f'The specified path: {file_path} is a directory but expected a file.'
        
        if not file_path.is_file():
            return f'The specified path is not a file: {file_path}'
        
        try:
            with file_path.open('r', encoding='utf-8') as f:
                file_content = f.read()
            
            tree = ast.parse(file_content)
            class_entries = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_name = node.name
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        docstring = "No docstring provided"

                    class_entries.append((class_name, docstring))
            
            if class_entries:
                result = ", ".join([f"`{name}` with docstring `{doc}`" for name, doc in class_entries])
                return f"The classes in `{file_name}` are {result}."
            else:
                return f"There are no classes in file {file_name}."
        
        except PermissionError:
            return f'Permission denied: Unable to access the file: {file_path}'
        except Exception as e:
            return f'An error occurred while processing the file: {e}'
