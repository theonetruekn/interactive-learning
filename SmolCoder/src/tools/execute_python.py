#TODO: Test
from typing import Any, List
import os 

from SmolCoder.src.tools.tool import Tool

class ExecutePythonCode(Tool):
    def __init__(self, path_to_file: str, filename: str):
        self.path_to_file = path_to_file
        self.filename = filename

    @property
    def name(self) -> str:
        return "Execute_Python_Code"

    @property
    def input_variables(self) -> List[str]:
        return ["python_code"]

    @property
    def desc(self) -> str:
        return "Executes the given python code"

    @property
    def example(self) -> str:
        raise NotImplementedError

    def __call__(self, python_code: str, cwd: str, logger) -> Any:
        """"
        Executes a string of Python code.

        Args:
            code_str: The string of Python code to execute.

        Returns:
            The output of the executed code, or None if there is no output.
        """
        with open(os.path.join(self.path_to_file, self.filename), "w+") as f:
            logger.debug("Saving python-code of ExecutePythonTool in the file %s in the location %s", self.filename, self.path_to_file)
            f.write(python_code)

        # Create a new namespace for the code to be executed in
        exec_namespace = {}
        exec(python_code, exec_namespace)
        # Get the result (if any) from the namespace
        result = exec_namespace.get("__result__", None)

        return result
