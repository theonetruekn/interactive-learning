import os
import pytest
import importlib.util
import inspect
from unittest.mock import patch, mock_open, MagicMock

from pathlib import Path 
import sys 
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))

import SmolCoder.src.tools.list_classes as im_list_classes

def test_get_class_summary():
    root = os.path.join(os.path.dirname(__file__), '../test_codebase')
    tool = im_list_classes.GetClassDocstrings(root)

    # Call the __call__ method
    result = tool("test.py")

    expected_output = [('MyClass', 'No docstring provided'), ('MyClass2'), 'No docstring provided']
    print(result)
    assert result == expected_output

if __name__ == "__main__":
    pytest.main()
    # test_get_class_summary()
