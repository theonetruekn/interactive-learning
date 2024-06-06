import ast
from pathlib import Path
from typing import List

from SmolCoder.src.tools.tool import Tool

class GetClassDocstrings(Tool):
    @property
    def name(self) -> str:
        return "List_Classes"
    
    @property
    def input_variables(self) -> List[str]:
        return ["file_name"]

    @property
    def desc(self) -> str:
        return "lists all the class names and their docstring comments in the specified Python file."

    def __init__(self, root_folder: Path):
        self.root_folder = Path(root_folder)
        if not self.root_folder.exists() or not self.root_folder.is_dir():
            raise ValueError(f'The specified root folder does not exist or is not a directory: {self.root_folder}')

    def __call__(self, file_name: str):
        file_path = self.root_folder / file_name
        
        if not file_path.exists():
            return f'The specified file does not exist: {file_path}'
        
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
                    docstring = ast.get_docstring(node) or "No docstring provided"
                    class_entries.append((class_name, docstring))
            
            return class_entries
        
        except PermissionError:
            return f'Permission denied: Unable to access the file: {file_path}'
        except Exception as e:
            return f'An error occurred while processing the file: {e}'
