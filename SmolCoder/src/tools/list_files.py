from pathlib import Path
from typing import List
import os 
from SmolCoder.src.tools.tool import Tool

class ListFiles(Tool):
    @property
    def name(self) -> str:
        return "List_Files"

    @property
    def input_variables(self) -> List[str]:
        return ["folder"]

    @property
    def desc(self) -> str:
        return "lists all the files and subfolder that are in the current folder."
    
    @property 
    def example(self):
        return f"{self.name}[.] to list the files of the current directory"

    #TODO: this should also work with "."
    def __call__(self, input_variables: List[str], cwd: Path, logger) -> str:
        full_path = cwd
        
        if not full_path.exists():
            return f'The specified folder does not exist: {full_path}'
        
        if not full_path.is_dir():
            return f'The specified path is not a folder: {full_path}'
        
        try:
            entries = []
            for entry in full_path.iterdir():
                entry_suffix = '/' if entry.is_dir() else ''
                entries.append(f"{entry.name}{entry_suffix}")
            return f"The entries in the directory `{str(full_path)}` are:\n" + "\n".join(entries)
        except PermissionError:
            return f'Permission denied: Unable to access the folder: {full_path}'
        except Exception as e:
            return f'An error occurred: {e}'
