# Agent-Computer Interface
# Manages tool use and augments prompts with auxiliary information, such as the current working directory

from typing import List
from pathlib import Path

from SmolCoder.src.toolkit import SearchMode, Toolkit


class AgentComputerInterface:

    def __init__(self, cwd:Path, tools:Toolkit) -> None:
        assert(cwd.exists())
        self.cwd = cwd
        self.tools = tools
        self.search_mode:SearchMode = SearchMode.EXACT
        self.finished = False

    def _generate_cwd_information(self) -> str:
        return f"(Current Working Directory: {str(self.cwd)})"

    def _change_cwd(self, new_dir:str) -> str:        
        path = Path(new_dir)
        
        if path.exists():
            if path.is_dir():
                self.cwd = path
                return f"Set the current working directory to {str(self.cwd)}"
            else:
                return f"Could not change the current working directory to {new_dir}, as it is a file, not a directory."
        else:
            return f"Could not change the current working directory to {new_dir}, as it does not exist."

    def get_observation(self, tool_name:str, input_variables: List[str]) -> str:
        if tool_name == "Move_to_Folder":
            assert len(input_variables) == 1, f"Input variables for `Move_to_Folder` are not of length 1: {input_variables}"
            new_dir = input_variables[0]
            return self._change_cwd(new_dir)
        else:
            if tool_name == "Finish":
                self.finished = True
            tool = self.tools.find_tool(tool_name)
            if (tool is None):
                obs =  f"No tool was found. Please choose one of the following tools: {self.tools.print_tool_short_descs()}" # TODO: Maybe add some stuff about "you can use fuzzy search too"
            elif (tool.number_of_input_variables() != len(input_variables)):
                obs = (
                    f"The tool expected {tool.number_of_input_variables()} parameters, but got {len(input_variables)}.\n"
                    f"The parameters that the tool {tool.name} needs are {tool.input_variables}"
                    )
            else:
                obs = tool(input_variables, cwd=self.cwd)

            obs += f"\n{self._generate_cwd_information()}\n"
            return obs
