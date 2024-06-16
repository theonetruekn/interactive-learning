import os
import pytest

from pathlib import Path 
import sys 
path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))

import SmolCoder.src.tools.list_classes as im_list_classes

def test_list_class_summary():
    root = os.path.join(os.path.dirname(__file__), '../test_codebase')
    tool = im_list_classes.GetClassDocstrings()

    # Call the __call__ method
    result = tool(["test.py"], cwd=Path(root))

    expected_output = [('MyClass', 'Class Docstring'), ('MyClass2', 'Another class Docstring')]
    print(result)
    assert result == expected_output

if __name__ == "__main__":
    pytest.main()
    # test_get_class_summary()
