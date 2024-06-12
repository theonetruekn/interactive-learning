import os
import pytest
import importlib.util
import inspect
from unittest.mock import patch, mock_open, MagicMock

from pathlib import Path 
import sys 
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))

import SmolCoder.src.tools.show_method as im_show_method

def test_list_class_summary():
    root = os.path.join(os.path.dirname(__file__), '../test_codebase')
    tool = im_show_method.ShowMethodBody()

    # Call the __call__ method
    result = tool("MyClass", "__init__", root)

    expected_output = """def __init__(self, one: str, two: int):
    \"\"\"
    Init the class. Careful: do not touch!
    \"\"\"
    self.one = one
    self.two = two"""

    print(result)
    print("----")
    print(expected_output)
    assert result == expected_output

if __name__ == "__main__":
    pytest.main()
