from typing import List

from SmolCoder.src.tools.tool import Tool

class MoveFolder(Tool):
    @property
    def name(self) -> str:
        return "Move_to_Folder"

    @property
    def input_variables(self) -> List[str]:
        return ["new_directory"]

    @property
    def desc(self) -> str:
        return "sets the current working directory to `new_directory`"

    @property
    def example(self) -> str:
        return f'{self.name}[new_directory]'
    
    @property
    def short_desc(self) -> str:
        return f'{self.name}[{",".join(self.input_variables)}]'
    
    def __call__(self, input_variables:List[str]):
        raise NotImplementedError("This method should never be called, ACI handles cwd changes.")
