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
            
            # If the agent gives this tool as input something else as "." ignore it
            # but give a message back
            if input_variables[0] != ".":
                output = f"The List_File tool got '{str(full_path)}' as input, but only takes '.' as input, the entries of the current working directory are: \n"
            else:
                output = f"The entries of the current working directory `{str(full_path)}` are:\n"

            return output + "\n".join(entries)

        except PermissionError:
            return f'Permission denied: Unable to access the folder: {full_path}'
        except Exception as e:
            return f'An error occurred: {e}'
