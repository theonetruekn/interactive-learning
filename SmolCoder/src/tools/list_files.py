from pathlib import Path
from typing import List

from SmolCoder.src.tools.tool import Tool

class ListFiles(Tool):
    @property
    def name(self) -> str:
        return "List_Files"
    
    @property 
    def example(self):
        raise NotImplementedError

    @property
    def input_variables(self) -> List[str]:
        return ["folder"]

    @property
    def desc(self) -> str:
        return "lists all the files and subfolder that are in the folder."

    def __call__(self, folder:Path, cwd: Path):
        try:
            folder_path = Path(folder)

            full_path = os.path.join(cwd, folder_path)
        except Exception as e:
            return "Something went wrong, when parsing the path to the folder location: " + str(e)

        if not full_path.exists():
            return f'The specified folder does not exist: {folder_path}'
    
        if not full_path.is_dir():
            return f'The specified path is not a folder: {folder_path}'
    
        try:
            entries = []
            for entry in full_path.iterdir():
                entry_type = 'folder' if entry.is_dir() else 'file'
                entries.append((entry.name, entry_type))
            return entries
        except PermissionError:
            return f'Permission denied: Unable to access the folder: {folder_path}'
        except Exception as e:
            return f'An error occurred: {e}'
