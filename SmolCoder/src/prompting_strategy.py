from abc import ABC, abstractmethod

from SmolCoder.src.llm_wrapper import LLM
from SmolCoder.src.agent import Token
from SmolCoder.src.toolkit import Toolkit

class PromptingStrategy(ABC):
    def __init__(self, lm: LLM, toolkit:Toolkit) -> None:
        self.lm = lm
        self.toolkit = toolkit

    @abstractmethod
    def __call__(self, prompt:str, max_iters:int = 3) -> str:
        pass
    
    @staticmethod
    def create(model:LLM, toolkit:Toolkit, strategy="ReAct"):
        if strategy == "ReAct":
            return ReAct(model, toolkit)
        else:
            raise ValueError

class ReAct(PromptingStrategy):

    def __init__(self, lm: LLM, toolkit:Toolkit) -> None:
        super().__init__(lm, toolkit)
        self.sysprompt = self._build_sysprompt()
    
    def _build_sysprompt(self) -> str:
        sysprompt = (
            "You will be given `question` and you will respond with `answer`.\n\n"
            "To do this, you will interleave Thought, Action, and Observation steps.\n\n"
            "Thought can reason about the current situation.\n" 
            "Action can be the following types:\n"
        )

        sysprompt += self.toolkit.pretty_print_tools()

        sysprompt += (
            "---\n\n"
            "Follow the following format:\n\n"
            "Thought: Reasoning which action to take to solve the task.\n"
            "Action: Always either "
        )

        sysprompt += self.toolkit.print_tool_short_descs()

        sysprompt += (
            "\nObservation: result of the previous Action\n"
            "Thought: next steps to take based on the previous Observation\n"
            "...\n"
            "until Action is of type `Finish`.\n\n"
            "---\n\n"
            "Question: "
        )

        return sysprompt

    def __call__(self, prompt: str, max_iters: int = 3, begin=True) -> str:
        if begin:
            prompt += self.sysprompt
        prompt += self.lm.query_completion(prompt)

        return prompt
