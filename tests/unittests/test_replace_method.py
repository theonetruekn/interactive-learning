import os
import unittest
from tempfile import TemporaryDirectory

from pathlib import Path 
import sys 
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))
from SmolCoder.src.tools.replace_method import ReplaceMethod

class TestReplaceMethod(unittest.TestCase):
    def setUp(self):
        self.tool = ReplaceMethod()

    def test_replace_method(self):
        # Create a temporary directory
        with TemporaryDirectory() as temp_dir:
            # Create a sample Python file with a class and method
            filename = "test_file.py"
            
            content = """class MyClass:
            def do_stuff(self) -> str:
                \"\"\"
                This method does stuff.
                \"\"\"
                return 'test'
            """
             
            new_method = """def do_stuff(self) -> str:
                return 'changed'
            """

            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Replace the method using the tool
            result = self.tool("MyClass", "do_stuff", new_method, temp_dir)
            
            # Verify that the method was replaced successfully
            self.assertIn("replaced successfully", result)

    def test_replace_method_class_not_found(self):
        # Create a temporary directory
        with TemporaryDirectory() as temp_dir:
            # Call the tool with a class that doesn't exist in any Python file in the directory
            result = self.tool("NonExistentClass", "test_method", "def test_method():\n    pass\n", temp_dir)
            # Verify that an appropriate error message is returned
            self.assertIn("Class 'NonExistentClass' not found", result)

if __name__ == "__main__":
    unittest.main()
