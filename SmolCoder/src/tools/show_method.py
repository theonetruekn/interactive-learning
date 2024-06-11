import ast
import os
from typing import List

from SmolCoder.src.tools.tool import Tool

class ShowMethodBody(Tool):
    @property
    def name(self) -> str:
        return "Show_Method_Body"
    
    @property
    def input_variables(self) -> List[str]:
        return ["class_name", "method_name"]

    @property
    def desc(self) -> str:
        return "returns a formatted String of the method body from the specified class and method name in `class_name` and `method_name`."

    def __init__(self):
        pass

    def __call__(self, class_name, method_name, cwd):
        for filename in os.listdir(cwd):
            full_path = os.path.join(cwd, filename)
            if os.path.isfile(full_path) and full_path.endswith(".py"):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    try:
                        tree = ast.parse(content, filename)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef) and node.name == class_name:
                                for class_node in node.body:
                                    if isinstance(class_node, ast.FunctionDef) and class_node.name == method_name:
                                        return ast.unparse(class_node)
                    except SyntaxError as e:
                        print(f"Error parsing {filename}: {e}")
        return None