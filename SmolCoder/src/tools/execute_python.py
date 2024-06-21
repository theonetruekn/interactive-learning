import io
import sys
from typing import List

from SmolCoder.src.tools.tool import Tool

class ExecutePythonCode(Tool):

    @property
    def name(self) -> str:
        return "Execute_Code"

    @property
    def input_variables(self) -> List[str]:
        return ["python_code"]

    @property
    def desc(self) -> str:
        return "executes the given python code and returns the value that is assigned to __result__"

    @property
    def example(self) -> str:
        raise NotImplementedError

    def __call__(self, input_variables: List[str]) -> str:
        python_code = input_variables[0]
        
        # Create a new namespace for the code to be executed in
        exec_namespace = {}

        # Capture the standard output
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout

        try:
            exec(python_code, exec_namespace)
        except Exception as e:
            output = str(e)
        else:
            output = new_stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        return output if output else "No output found"
