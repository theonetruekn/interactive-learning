from pathlib import Path

from SmolCoder.src.tools.tool import Tool

class ListFiles(Tool):
    name = "List_Files"
    input_variable = "folder" 
    desc =  "lists all the files and subfolder that are in the folder."
    
    def __init__(self):
        pass

    def __call__(self, folder:Path):
        folder_path = Path(folder)
    
        if not folder_path.exists():
            return f'The specified folder does not exist: {folder_path}'
    
        if not folder_path.is_dir():
            return f'The specified path is not a folder: {folder_path}'
    
        try:
            entries = []
            for entry in folder_path.iterdir():
                entry_type = 'folder' if entry.is_dir() else 'file'
                entries.append((entry.name, entry_type))
            return entries
        except PermissionError:
            return f'Permission denied: Unable to access the folder: {folder_path}'
        except Exception as e:
            return f'An error occurred: {e}'