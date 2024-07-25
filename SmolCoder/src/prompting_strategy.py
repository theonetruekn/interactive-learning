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
    def create(model:LLM, toolkit:Toolkit, strategy="ReAct", mode:int = 2):
        if strategy == "ReAct":
            return ReAct(name=strategy, lm=model, toolkit=toolkit, mode=mode)
        else:
            raise ValueError

class ReAct(PromptingStrategy):
    SYSPROMPT_TOKEN = "[Sysprompt]"
    THOUGHT_TOKEN = "[Thought]"
    ACTION_TOKEN = "[Action]"
    OBSERVATION_TOKEN = "[Observation]"

    def __init__(self, name:str, lm: LLM, toolkit:Toolkit, mode:int = 2) -> None:
        """
        Args:
            mode (int): 0 for github_issue_mode, 1 for repoduce_error_mode, 2 for ReAct Mode
        """
        super().__init__(name, lm, toolkit)
        self._mode = mode 
        self._sysprompt = self._build_sysprompt()

    def _build_sysprompt(self) -> str:
        sysprompt = self.SYSPROMPT_TOKEN
        
        if self._mode == 0:
            sysprompt += "You will be given a description of a `github issue` and your task is, to solve this issue, first you should use tools to investiaget the repo to find the sectio where the error occurs and then you should replace this section with the correct code.\n\n"
        elif self._mode == 1:
            sysprompt += "You will be given a description of a `github issue` and your task is, to reproduce this issue by using the available tools to you.\n\n"
        elif self._mode == 2:
            sysprompt += "You will be given `question` and you will respond with `answer`.\n\n"
        else:
            raise ValueError("The Mode: " + str(self._mode) + " is not a valid mode for ReAct.")

        sysprompt += (
            "To do this, you will interleave Thought, Action, and Observation steps.\n\n"
            "Thought can reason about the current situation.\n" 
            "Action can be the following types, \n"
        )

        sysprompt += self.toolkit.pretty_print_tools()
        sysprompt += "\n Input variables of the tools do not need quotation marks around them. In addition, do NOT use the `finish` tool before having made all changes to remedy the issue."
        sysprompt += (
            "\n---\n\n"
            "Follow the following format:\n\n"
            f"{self.THOUGHT_TOKEN}Reasoning which action to take to solve the task.\n"
            f"{self.ACTION_TOKEN}Always either "
        )

        sysprompt += self.toolkit.print_tool_short_descs()

        sysprompt += (
            f"\n{self.OBSERVATION_TOKEN}result of the previous Action\n"
            f"{self.THOUGHT_TOKEN}next steps to take based on the previous Observation\n"
            "...\n"
            f"until {self.ACTION_TOKEN} is of type `Finish`. Do not use any special formatation such as markdown.\n\n"
            "---\n\n"
        )

        sysprompt += self.SYSPROMPT_TOKEN

        return sysprompt

    def __call__(self, prompt: str, begin=False) -> str:
        if begin:
            prompt = self.sysprompt + prompt + "\n"
        
        prompt += self.lm.query_completion(prompt, stop_token=self.OBSERVATION_TOKEN)
        return prompt
