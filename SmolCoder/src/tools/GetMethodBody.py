import os
import ast

class GetMethodBody:
    name = "GetMethodBody"
    input_variable = "class_name, method_name"
    desc =  """
            Return a formatted String of the method body from 
            the specified class and method name in `class_name` and `method_name`.
            Example use: GetMethodBody("MyClassName", "MyMethodName")
            """
    
    def __init__(self, root):
        self.root = root

    def __call__(self, class_name, method_name):
        for filename in os.listdir(self.root):
            full_path = os.path.join(self.root, filename)
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