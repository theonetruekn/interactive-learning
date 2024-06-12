import os
import pytest
import importlib.util
import inspect
from unittest.mock import patch, mock_open, MagicMock

from pathlib import Path 
import sys 
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))

import SmolCoder.src.tools.list_files as im_list_files

def test_list_class_summary():
    root = os.path.join(os.path.dirname(__file__), '../test_codebase')
    tool = im_list_files.ListFiles()

    # Call the __call__ method
    result = tool(root)

    expected_output = [('__pycache__', 'folder'), ('test.py', 'file')]
    print(result)
    assert result == expected_output

if __name__ == "__main__":
    pytest.main()
