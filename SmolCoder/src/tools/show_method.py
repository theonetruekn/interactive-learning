import ast
import os
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
    def example():
        pass

    @property
    def desc(self) -> str:
        return "returns a formatted String of the method body from the specified class and method name in `class_name` and `method_name`."

    def __init__(self):
        pass

    def __call__(self, class_name, method_name, cwd):
            # Change the current working directory
        os.chdir(cwd)
        
        # Add the current working directory to the system path
        sys.path.insert(0, cwd)
        
        # Iterate over all Python files in the directory
        for root, _, files in os.walk(cwd):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    # Create module name from file path
                    module_name = os.path.splitext(os.path.relpath(file_path, cwd))[0].replace(os.sep, '.')
                    
                    # Try to import the module
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, file_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[module_name] = module
                            spec.loader.exec_module(module)
                    except Exception as e:
                        print(f"Failed to import {module_name}: {e}")
                        continue
                    
                    # Check if the class is in the module
                    if hasattr(module, class_name):
                        class_obj = getattr(module, class_name)
                        # Check if the method is in the class
                        if hasattr(class_obj, method_name):
                            method_obj = getattr(class_obj, method_name)
                            # Get the source code of the method
                            try:
                                method_source = inspect.getsource(method_obj)

                                method_source = textwrap.dedent(method_source)
                                
                                lines = method_source.split('\n')
                                if lines and not lines[-1].strip():
                                    method_source = '\n'.join(lines[:-1])
                                
                                return method_source
                            except TypeError:
                                return f"Could not retrieve source code for {method_name}"
            
            return f"Class {class_name} with method {method_name} not found in any module in {cwd}"
        # for filename in os.listdir(cwd):
        #     full_path = os.path.join(cwd, filename)
        #     if os.path.isfile(full_path) and full_path.endswith(".py"):
        #         with open(full_path, 'r', encoding='utf-8') as f:
        #             content = f.read()
        #             try:
        #                 tree = ast.parse(content, filename)
        #                 for node in ast.walk(tree):
        #                     if isinstance(node, ast.ClassDef) and node.name == class_name:
        #                         for class_node in node.body:
        #                             if isinstance(class_node, ast.FunctionDef) and class_node.name == method_name:
        #                                 return ast.unparse(class_node)
        #             except SyntaxError as e:
        #                 print(f"Error parsing {filename}: {e}")
        # return None
