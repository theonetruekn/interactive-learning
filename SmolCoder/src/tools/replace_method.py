import os
import ast
from pathlib import Path
from typing import List

from SmolCoder.src.tools.tool import Tool

class ReplaceMethod(Tool):
    @property
    def name(self) -> str:
        return "Replace_Method"
    
    @property 
    def example(self):
        new_method = """
def do_stuff():
    test = 5 + 3

    print("test: " + str(test))
    
    return test
"""
        return f"{self.name}[do_stuff, {new_method}]"

    @property
    def input_variables(self) -> List[str]:
        return ["class_name", "method_name", "new_method"]

    @property
    def desc(self) -> str:
        return "replaces the specified method `method_name` in the `class_name` with `new_method`."

    def __call__(self, input_variables:List[str], cwd:Path, logger) -> str:
        class_name, method_name, new_method = input_variables[0], input_variables[1], input_variables[2]
        # TODO: Enable this when implemented
        # assert(self._lint(new_method))
        for filename in os.listdir(cwd):
            full_path = os.path.join(cwd, filename)

            if logger:
                logger.debug("ReplaceMethod opening the file %s", full_path)

            if os.path.isfile(full_path) and full_path.endswith(".py"):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    try:
                        tree = ast.parse(content, filename)
                        for node in tree.body:
                            if isinstance(node, ast.ClassDef) and node.name == class_name:
                                for class_node in node.body:
                                    if isinstance(class_node, ast.FunctionDef) and class_node.name == method_name:

                                        if logger:
                                            logger.debug("Found the to be replaced method.")

                                        # Remove the existing method
                                        node.body.remove(class_node)
                                        # Add the new method
                                        node.body.extend(ast.parse(new_method).body)
                                        modified_code = ast.unparse(tree)
                                        with open(full_path, 'w', encoding='utf-8') as f:
                                            f.write(modified_code)
                                        return f"Method '{method_name}' in class '{class_name}' replaced successfully in file '{filename}'."
                    except SyntaxError as e:
                        return f"Error parsing file '{filename}': {e}"
        return f"Error: Class '{class_name}' not found in any Python files in the directory '{cwd}'."

    def _lint(self, method:str) -> str:
        raise NotImplementedError
