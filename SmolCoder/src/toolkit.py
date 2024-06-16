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
        normalized_query = query.lower()
        
        if mode == SearchMode.EXACT:
            return self._tools.get(normalized_query)
        elif mode == SearchMode.FUZZY:
            raise NotImplementedError
        else:
            return None

    def pretty_print_tools(self) -> str:
        try:
            return "\n".join(
            f"({i}) {tool.short_desc}, which {tool.desc}. Example use: {tool.example}"
            for i, (_, tool) in enumerate(self._tools.items(), start=1))
        except NotImplementedError:
            print("Example function, not implemented")
            return "\n".join(
            f"({i}) {tool.short_desc}, which {tool.desc}."
            for i, (_, tool) in enumerate(self._tools.items(), start=1))

    def print_tool_short_descs(self) -> str:
        return " or ".join([f"{tool.short_desc}" for _, tool in self._tools.items()])
        
