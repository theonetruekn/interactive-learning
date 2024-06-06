# Agent-Computer Interface
# Manages tool use and augments prompts with auxiliary information, such as the current working directory

from pathlib import Path

from SmolCoder.src.toolkit import Toolkit


class AgentComputerInterface:

    def __init__(self, cwd:Path, tools:Toolkit) -> None:
        assert(cwd.exists())
        self.cwd = cwd
        self.tools = tools

    def _generate_cwd_information(self) -> str:
        return f"(Current Working Directory: {self.cwd}"