from enum import Enum
from typing import Dict, List, Optional

from SmolCoder.src.tools.tool import Tool

class SearchMode(Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"

class Toolkit:
    def __init__(self, tools:List[Tool]) -> None:
        self._tools = self._construct_tools(tools)
    
    def _construct_tools(self, tools:List[Tool]) -> Dict[str, Tool]:
        return {tool.name:tool for tool in tools}
    
    def find_tool(self, query:str, mode:SearchMode=SearchMode.EXACT) -> Optional[Tool]:
        raise NotImplementedError

    def pretty_print_tools(self) -> str:
        return "\n".join(
        f"({i}) {tool.short_desc}, which {tool.desc}. Example use: {tool.example}"
        for i, (_, tool) in enumerate(self._tools.items(), start=1)
    )

    def print_tool_short_descs(self) -> str:
        return " or ".join([f"{tool.short_desc}" for _, tool in self._tools.items()])
        