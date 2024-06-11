# Agent-Computer Interface
# Manages tool use and augments prompts with auxiliary information, such as the current working directory

from typing import List, Tuple
from pathlib import Path

from SmolCoder.src.toolkit import Toolkit


class AgentComputerInterface:

    def __init__(self, cwd:Path, tools:Toolkit) -> None:
        assert(cwd.exists())
        self.cwd = cwd
        self.tools = tools

    def _generate_cwd_information(self) -> str:
        return f"(Current Working Directory: {self.cwd}"
    
    def _tokenize(self, action_sequence: str) -> Tuple[str, List[str]]:
        raise NotImplementedError

    def _change_cwd(self, new_dir:str) -> str:        
        path = Path(new_dir)
        
        if path.exists():
            if path.is_dir():
                self.cwd = path
                return f"Set the current working directory to {self.cwd}"
            else:
                return f"Could not change the current working directory to {new_dir}, as it is a file, not a directory."
        else:
            return f"Could not change the current working directory to {new_dir}, as it does not exist."

    def get_observation(self, action_sequence: str) -> str:
        tool_name, input_variables = self._tokenize(action_sequence)
        if tool_name == "Move_to_Folder":
            assert len(input_variables) == 1, f"Input variables for `Move_to_Folder` are not of length 1: {input_variables}"
            new_dir = input_variables[0]
            return self._change_cwd(new_dir)
        else:
            tool = self.tools.find_tool(tool_name)
            assert (tool is not None), "No tool was found" # TODO: Maybe add some stuff about "you can use fuzzy search too"
            return tool(input_variables, cwd=self.cwd)