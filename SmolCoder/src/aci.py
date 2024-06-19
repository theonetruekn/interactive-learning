# Agent-Computer Interface
# Manages tool use and augments prompts with auxiliary information, such as the current working directory

import re

from typing import List, Tuple
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
    
    def _tokenize(self, action_sequence: str) -> Tuple[str, List[str]]:
        action_sequence = action_sequence.replace("Action:", "").strip()
        
        match = re.match(r'(\w+.*)\[(.*)\]', action_sequence)
        if match:
            tool_name = match.group(1).strip()
            args = match.group(2).split(', ')
            
            if tool_name.lower() == "finish":
                args = [match.group(2)]
            return tool_name, args
        else:
            parts = action_sequence.split()
            if len(parts) > 1:
                tool_name = parts[0].strip()
                args = parts[1:]
                return tool_name, args

        raise ValueError("The Tool does not match the required format: tool_name[input_variable_1,...,input_variable_n].")

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

    def get_observation(self, action_sequence: str) -> Tuple[str, str]:
        try:
            tool_name, input_variables = self._tokenize(action_sequence)
        except ValueError as e:
            return str(e), ""

        tool_name, input_variables = self._tokenize(action_sequence)
        if tool_name == "Move_to_Folder":
            assert len(input_variables) == 1, f"Input variables for `Move_to_Folder` are not of length 1: {input_variables}"
            new_dir = input_variables[0]
            return "", self._change_cwd(new_dir)
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
                obs = self._remove_encapsulating_quotes(tool(input_variables, cwd=self.cwd))

            cwd_msg = f"\n{self._generate_cwd_information()}\n"
            return obs, cwd_msg 

    def _remove_encapsulating_quotes(self, s) -> str:
        if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
            return s[1:-1]
        return s
