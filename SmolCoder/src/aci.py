# Agent-Computer Interface
# Manages tool use and augments prompts with auxiliary information, such as the current working directory

from typing import List, Tuple
from pathlib import Path

from SmolCoder.src.toolkit import SearchMode, Toolkit


class AgentComputerInterface:

    def __init__(self, cwd:Path, tools:Toolkit, logger) -> None:
        assert(cwd.exists())
        self.cwd = cwd
        self.tools = tools
        self.search_mode:SearchMode = SearchMode.EXACT
        self.finished = False
        self.logger = logger 

    def _generate_cwd_information(self) -> str:
        return f"(Current Working Directory: {str(self.cwd)}) \n"

    def _change_cwd(self, new_dir:str) -> str: 
        if self.logger is not None:
            self.logger.debug("Activated Move_to_Folder tool")
            self.logger.debug("current working directory: " + str(self.cwd))

        path = self.cwd / Path(new_dir)

        if self.logger is not None:
            self.logger.debug("New directory path: " + str(path))
        
        if path.exists():
            if self.logger is not None:
                print("The New directory path doesn't exist.")
            if path.is_dir():
                self.cwd = path
                return f"Set the current working directory to `{str(self.cwd)}`."
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
            tool = self.tools.find_tool(tool_name)
            if (tool is None):
                obs =  (
                    f"No tool was found. Please choose one of the following tools: {self.tools.print_tool_short_descs()}."
                    "Remember that to use a tool it has to follow the format of Tool_Name[arg1, arg2, ...]."
                )
            elif (not tool.valid_params(input_variables)):
                obs = (
                    f"The tool expected {tool.number_of_input_variables()} parameters, but got {len(input_variables)}.\n"
                    f"The parameters that the tool {tool.name} needs are {tool.input_variables}"
                    )
            else:
                if tool_name == "Finish":
                    self.finished = True
                input_variables = [self._remove_encapsulating_quotes(i_v) for i_v in input_variables]
                obs = tool(input_variables, cwd=self.cwd, logger=self.logger)
            
            if not self.finished:
                cwd_msg = f"\n{self._generate_cwd_information()}\n"
                obs += cwd_msg

            return obs

    def _remove_encapsulating_quotes(self, s) -> str:
        if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
            if self.logger is not None:
                self.logger.debug("\nRemoving encapsulating quotation marks!\n")
            return s[1:-1]
        return s
