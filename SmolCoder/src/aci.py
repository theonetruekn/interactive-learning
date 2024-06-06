# Agent-Computer Interface
# Manages tool use and augments prompts with auxiliary information, such as the current working directory

from pathlib import Path


class AgentComputerInterface:

    def __init__(self, cwd:Path, tools:dict) -> None:
        assert(cwd.exists())
        self.cwd = cwd
        self.tools = self._init_tools(tools)

    def _init_tools(self, tools:dict):
        #TODO
        pass

    def _generate_cwd_information(self):
        return f"(Current Working Directory: {self.cwd}"