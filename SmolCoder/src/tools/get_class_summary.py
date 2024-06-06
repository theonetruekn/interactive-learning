import os
import inspect
import importlib.util
from typing import List

from SmolCoder.src.tools.tool import Tool

class GetClassSummary(Tool):    
    @property
    def name(self) -> str:
        return "Get_Class_Summary"
    
    @property
    def input_variable(self) -> List[str]:
        return ["class_name"]

    @property
    def desc(self) -> str:
        return "Returns a formatted string of methods heads from the class specified in `class_name`."

    def __call__(self, class_name, root):
        formatted_methods = []

        for filename in os.listdir(root):
            full_path = os.path.join(root, filename)
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