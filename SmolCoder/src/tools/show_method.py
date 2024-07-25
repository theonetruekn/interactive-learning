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
        return f'{self.name}[class_name, method_name]'

    @property
    def desc(self) -> str:
        return "returns a formatted String of the method body from the specified class and method name in `class_name` and `method_name`."

    def __call__(self, input_variables: List[str], cwd: Path, logger) -> str:
        class_name, method_name = input_variables[0], input_variables[1]
        for root, _, files in os.walk(cwd):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        try:
                            file_content = f.read()
                            tree = ast.parse(file_content, filename=file_path)
                            
                            for node in ast.walk(tree):
                                if isinstance(node, ast.ClassDef) and node.name == class_name:
                                    if logger:
                                        logger.log(f"Found the correct class {class_name} in the file {file_path}")
                                    
                                    for class_node in node.body:
                                        if isinstance(class_node, ast.FunctionDef) and class_node.name == method_name:
                                            if logger:
                                                logger.log(f"Found the correct method {method_name} in the class {class_name}")
                                            
                                            # Retrieve the source code of the method
                                            method_source_lines = file_content.splitlines()[class_node.lineno-1:class_node.end_lineno]
                                            method_source = '\n'.join(method_source_lines)
                                            return f"```\n{method_source.strip()}\n```"
                        except Exception as e:
                            print(f"Failed to parse {file_path}: {e}")
        
        return f"Class {class_name} with method {method_name} not found in any module in {cwd}"
