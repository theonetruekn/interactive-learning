from enum import Enum
from typing import Dict, List, Optional

from SmolCoder.src.tools.tool import Tool

class SearchMode(Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"

class Toolkit:
    def __init__(self, tools:List[Tool]) -> None:
        self._tools = self._construct_tools(tools)
    
    def _construct_tools(self, tools:List[Tool]) -> Dict:
        return {tool.name:tool for tool in tools}
    
    def find_tool(self, query:str, mode:SearchMode=SearchMode.EXACT) -> Optional[Tool]:
        raise NotImplementedError
