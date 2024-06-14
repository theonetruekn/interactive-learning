import os
import pytest
import importlib.util
import inspect
from unittest.mock import patch, mock_open, MagicMock

from pathlib import Path 
import sys 
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))

import SmolCoder.src.tools.execute_python as im_execute_python

def test_get_class_summary():
    temp = os.path.join(os.path.dirname(__file__), '../temp/')

    tool = im_execute_python.ExecutePythonCode(temp, "temp.py")
    root = os.path.join(os.path.dirname(__file__), '../test_codebase')
        
    # Example usage
    code_str = (
            "# This is the Python code to be executed"
            "a = 10"
            "b = 20"
            "__result__ = a + b"
    )

    # Call the __call__ method
    result = tool(code_str)

    expected_output = 30
    assert result == expected_output

if __name__ == "__main__":
    pytest.main()
