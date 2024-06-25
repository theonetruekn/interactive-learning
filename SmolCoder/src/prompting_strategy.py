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
    def create(model:LLM, toolkit:Toolkit, strategy="ReAct", gihub_issue_mode:bool = False):
        if strategy == "ReAct":
            return ReAct(name=strategy, lm=model, toolkit=toolkit, gihub_issue_mode=gihub_issue_mode)
        else:
            raise ValueError

class ReAct(PromptingStrategy):

    def __init__(self, name:str, lm: LLM, toolkit:Toolkit, gihub_issue_mode:bool = False) -> None:
        super().__init__(name, lm, toolkit)
        self._github_issue_mode = gihub_issue_mode 
        self._sysprompt = self._build_sysprompt()

    def _build_sysprompt(self) -> str:
        if self._github_issue_mode:
            prompt = "You will be given a description of a `github issue` and your task is, to solve this issue with the available tools.\n\n"
        else: 
            prompt = "You will be given `question` and you will respond with `answer`.\n\n"

        sysprompt = prompt + (
            "To do this, you will interleave Thought, Action, and Observation steps.\n\n"
            "Thought can reason about the current situation.\n" 
            "Action can be the following types, \n"
        )

        sysprompt += self.toolkit.pretty_print_tools()
        sysprompt += "\n Input variables of the tools do not need quotation marks around them. In addition, do NOT use the `finish` tool before having made all changes to remedy the issue."
        sysprompt += (
            "\n---\n\n"
            "Follow the following format:\n\n"
            "Thought: Reasoning which action to take to solve the task.\n"
            "Action: Always either "
        )

        sysprompt += self.toolkit.print_tool_short_descs()

        sysprompt += (
            "\nObservation: result of the previous Action\n"
            "Thought: next steps to take based on the previous Observation\n"
            "...\n"
            "until Action is of type `Finish`. Do not use any special formatation such as markdown.\n\n"
            "---\n\n"
        )

        return sysprompt

    def __call__(self, prompt: str, begin=False) -> str:
        if begin:
            prompt = self.sysprompt + prompt + "\n"
        
        prompt += self.lm.query_completion(prompt, stop_token="Observation: ")
       
        return prompt
