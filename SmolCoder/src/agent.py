from enum import Enum
from pathlib import Path

from SmolCoder.src.prompting_strategy import PromptingStrategy
from SmolCoder.src.aci import AgentComputerInterface
from SmolCoder.src.llm_wrapper import LLM
from SmolCoder.src.toolkit import Toolkit

class Token(Enum):
    SYSPROMPT = "SYSPROMPT"
    QUESTION = "QUESTION"
    ACTION = "ACTION"
    THOUGHT = "THOUGHT"
    OBSERVATION = "OBSERVATION"


class SmolCoder:
    """
    This class handles the communication between the prompting strategy and the agent-computer-interface.
    """
    def __init__(self, model:LLM, codebase_dir:Path, toolkit:Toolkit, prompting_strategy:str = "ReAct") -> None:
        self.ACI = AgentComputerInterface(cwd=codebase_dir, tools=toolkit)
        self.prompting_strategy = PromptingStrategy.create(model, strategy=prompting_strategy, toolkit=toolkit)
    
    def __call__(self, userprompt: str, max_calls:int = 10) -> str:
        trajectory = ""
        for i in range(max_calls):
            start = False
            if i == 1:
                start = True
            trajectory, action_sequence = self.prompting_strategy(prompt=userprompt, begin=start)
            obs = self.ACI.get_observation(action_sequence)
            trajectory += obs
        return trajectory