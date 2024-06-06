import os
import ast

class ReplaceMethod:
    name = "ReplaceMethod"
    input_variable = "class_name, method_name, new_method"
    desc =  """
            Replaces the specified method `method_name` in the `class_name` with `new_method`.
            Example Use: ReplaceMethod("MyClassName", "old_method", "new_method")
            """
    
    def __init__(self, root):
        self.root = root

    def __call__(self, class_name, method_name, new_method):
        for filename in os.listdir(self.root):
            full_path = os.path.join(self.root, filename)
            if os.path.isfile(full_path) and full_path.endswith(".py"):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    try:
                        tree = ast.parse(content, filename)
                        for node in tree.body:
                            if isinstance(node, ast.ClassDef) and node.name == class_name:
                                for class_node in node.body:
                                    if isinstance(class_node, ast.FunctionDef) and class_node.name == method_name:
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
        return f"Error: Class '{class_name}' not found in any Python files in the directory '{self.root}'."
