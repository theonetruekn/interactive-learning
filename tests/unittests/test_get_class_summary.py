import os
import pytest
import importlib.util
import inspect
from unittest.mock import patch, mock_open, MagicMock

from pathlib import Path 
import sys 
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))

import SmolCoder.src.tools.get_class_summary as im_class_summary

def test_get_class_summary():
    tool = im_class_summary.GetClassSummary()
    root = os.path.join(os.path.dirname(__file__), '../test_codebase')

    result = tool(["MyClass"], root)

    expected_output = (
        "def __init__(self, one: str, two: int):\n"
        "    \"\"\"\n"
        "    Init the class. Careful: do not touch!\n"
        "    \"\"\"\n\n"
        "def do_stuff(self) -> str:\n"
        "    \"\"\"\n"
        "    This method does stuff.\n"
        "    \"\"\""
    )
    assert result == expected_output

if __name__ == "__main__":
    pytest.main()
