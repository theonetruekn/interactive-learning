from abc import ABC, abstractmethod

from SmolCoder.src.llm_wrapper import LLM

class PromptingStrategy(ABC):
    def __init__(self, lm: LLM) -> None:
        self.lm = lm

    @abstractmethod
    def __call__(self, prompt:str, max_iters:int = 3) -> str:
        pass
    
    @staticmethod
    def create(model:LLM, strategy="ReAct"):
        if strategy == "ReAct":
            return ReAct(model)
        else:
            raise ValueError

class ReAct(PromptingStrategy):
    def __call__(self, prompt: str, max_iters: int = 3) -> str:
        raise NotImplementedError