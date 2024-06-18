import os
import inspect
import importlib.util
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

    def __call__(self, input_variables:List[str], cwd:Path):
        class_name = input_variables[0]
        formatted_methods = []

        for filename in os.listdir(cwd):
            full_path = os.path.join(cwd, filename)
            if os.path.isfile(full_path) and full_path.endswith(".py"):
                module_name = os.path.splitext(filename)[0]
                spec = importlib.util.spec_from_file_location(module_name, full_path)
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                except Exception as e:
                    print(f"Error importing {filename}: {e}")
                    continue
                
                if hasattr(module, class_name):
                    cls = getattr(module, class_name)
                    if inspect.isclass(cls):
                        for name, member in inspect.getmembers(cls, inspect.isfunction):
                            if member.__qualname__.startswith(class_name):
                                sig = inspect.signature(member)
                                method_head = f"def {name}{sig}:"
                                docstring = inspect.getdoc(member) or ""
                                if docstring:
                                    indented_docstring = self._indent(docstring, 4)
                                    docstring = f'    """\n{indented_docstring}\n    """'
                                formatted_methods.append(f"{method_head}\n{docstring}")
        
        return "\n\n".join(formatted_methods)

    def _indent(self, text, spaces):
        indent = ' ' * spaces
        return '\n'.join(indent + line if line.strip() else line for line in text.split('\n'))