from typing import Any, List
from SmolCoder.src.tools.tool import Tool

class Finish(Tool):
    @property
    def name(self) -> str:
        return "Finish"

    @property
    def input_variables(self) -> List[str]:
        return ["answer"]

    @property
    def desc(self) -> str:
        return "finishes the program."

    @property
    def example(self) -> str:
        raise NotImplementedError
    
    @property
    def short_desc(self) -> str:
        return f'{self.name}[{",".join(self.input_variables)}]'
    
    def __call__(self, answer: str, cwd) -> Any:
        return answer
