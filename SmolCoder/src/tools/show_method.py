import ast
import os
from pathlib import Path
from typing import List
import inspect 
import importlib 
import sys 
import textwrap

from SmolCoder.src.tools.tool import Tool

class ShowMethodBody(Tool):
    @property
    def name(self) -> str:
        return "Show_Method_Body"
    
    @property
    def input_variables(self) -> List[str]:
        return ["class_name", "method_name"]
    
    @property 
    def example(self):
        raise NotImplementedError

    @property
    def desc(self) -> str:
        return "returns a formatted String of the method body from the specified class and method name in `class_name` and `method_name`."

    def __call__(self, input_variables: List[str], cwd: Path) -> str:
        class_name, method_name = input_variables[0], input_variables[1]
        for root, _, files in os.walk(cwd):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    module_name = os.path.splitext(os.path.relpath(file_path, cwd))[0].replace(os.sep, '.')
                    
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, file_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[module_name] = module
                            spec.loader.exec_module(module)
                    except Exception as e:
                        print(f"Failed to import {module_name}: {e}")
                        continue
                    
                    if hasattr(module, class_name):
                        class_obj = getattr(module, class_name)
                        if hasattr(class_obj, method_name):
                            method_obj = getattr(class_obj, method_name)
                            try:
                                method_source = inspect.getsource(method_obj)
                                method_source = textwrap.dedent(method_source)
                                return method_source.strip()
                            except TypeError:
                                return f"Could not retrieve source code for {method_name}"
        
        return f"Class {class_name} with method {method_name} not found in any module in {cwd}"