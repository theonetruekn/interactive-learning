import sys
from typing import List

from SmolCoder.src.tools.tool import Tool

class HumanInteraction(Tool):

    @property
    def name(self) -> str:
        return "Human_Interaction"

    @property
    def input_variables(self) -> List[str]:
        return ["asking_for_help_message"]

    @property
    def desc(self) -> str:
        return "asks the controlling Human for help on your task by providing them with your `asking_for_help_message`."

    @property
    def example(self) -> str:
        return f'{self.name}[asking_for_help_message]'

    def __call__(self, input_variables: List[str]) -> str:
        
        try:
            human_help = input(input_variables[0])
        except Exception as e:
            return f"an error has occured while trying to get help from the human: {str(e)}"

        return human_help
