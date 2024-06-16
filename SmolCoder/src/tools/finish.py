from typing import Any, List
from SmolCoder.src.tools.tool import Tool

class Tool(Tool):
    @property
    def name(self) -> str:
        return "Finish"

    @property
    def input_variables(self) -> List[str]:
        return ["Answer"]

    @property
    @abstractmethod
    def desc(self) -> str:
        return "Finishes the program"

    @property
    def example(self) -> str:
        raise NotImplementedError
    
    @property
    def short_desc(self) -> str:
        return f'{self.name}[{",".join(self.input_variables)}]'
    
    @abstractmethod
    def __call__(self, answer: str) -> Any:
        return answer
