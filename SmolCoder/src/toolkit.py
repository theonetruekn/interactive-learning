from enum import Enum
from typing import Dict, List, Optional, Set

from SmolCoder.src.tools.tool import Tool

class SearchMode(Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"

class Toolkit:
    def __init__(self, tools:List[Tool]) -> None:
        self._tools = self._construct_tools(tools)
    
    def _construct_tools(self, tools:List[Tool]) -> Dict[str, Tool]:
        return {tool.name.lower(): tool for tool in tools}
    
    def find_tool(self, query:str, mode:SearchMode=SearchMode.EXACT) -> Optional[Tool]:
        normalized_query = query.lower()
        
        if mode == SearchMode.EXACT:
            return self._tools.get(normalized_query)
        elif mode == SearchMode.FUZZY:
            raise NotImplementedError
        else:
            return None

    def pretty_print_tools(self) -> str:
            return "\n".join(
            f"({i}) {tool.short_desc}, which {tool.desc} Example use: {tool.example}"
            for i, (_, tool) in enumerate(self._tools.items(), start=1))

    def print_tool_short_descs(self) -> str:
        return " or ".join([f"{tool.short_desc}" for _, tool in self._tools.items()])

    def get_possible_actions(self) -> Set[str]:
        return set(self._tools.keys())
        
