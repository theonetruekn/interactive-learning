from abc import ABC, abstractmethod

from SmolCoder.src.llm_wrapper import LLM
from SmolCoder.src.toolkit import Toolkit

class PromptingStrategy(ABC):
    def __init__(self, name:str, lm: LLM, toolkit:Toolkit) -> None:
        self.name = name
        self.lm = lm
        self.toolkit = toolkit
        self._sysprompt = "Placeholder"

    @property
    def sysprompt(self):
        return self._sysprompt

    @abstractmethod
    def __call__(self, prompt:str) -> str:
        pass
    
    @staticmethod
    def create(model:LLM, toolkit:Toolkit, strategy="ReAct"):
        if strategy == "ReAct":
            return ReAct(name=strategy, lm=model, toolkit=toolkit)
        else:
            raise ValueError

class ReAct(PromptingStrategy):

    THOUGHT_TOKEN = "Thought:"
    ACTION_TOKEN = "Action:"
    OBSERVATION_TOKEN = "Observation:"

    def __init__(self, name:str, lm: LLM, toolkit:Toolkit) -> None:
        super().__init__(name, lm, toolkit)
        self._sysprompt = self._build_sysprompt()

    def _build_sysprompt(self) -> str:
        sysprompt = (
            "You will be given `question` and you will respond with `answer`.\n\n"
            "To do this, you will interleave Thought, Action, and Observation steps.\n\n"
            "Thought can reason about the current situation.\n" 
            "Action can be the following types, \n"
        )

        sysprompt += self.toolkit.pretty_print_tools()
        sysprompt += "\nInput variables of the tools do not need quotation marks around them."
        sysprompt += (
            "\n---\n\n"
            "Follow the following format:\n\n"
            f"{self.THOUGHT_TOKEN} Reasoning which action to take to solve the task.\n"
            f"{self.ACTION_TOKEN} Always either "
        )

        sysprompt += self.toolkit.print_tool_short_descs()

        sysprompt += (
            f"\n{self.OBSERVATION_TOKEN} result of the previous Action\n"
            f"{self.THOUGHT_TOKEN} next steps to take based on the previous Observation\n"
            "...\n"
            "until Action is of type `Finish`.\n\n"
            "---\n\n"
        )

        return sysprompt

    def __call__(self, prompt: str, begin=False) -> str:
        if begin:
            prompt = self.sysprompt + prompt + "\n"
        
        prompt += self.lm.query_completion(prompt, stop_token=self.OBSERVATION_TOKEN)
        prompt += " " #adds whitespace after "Observation:"
       
        return prompt
