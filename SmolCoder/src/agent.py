import re

from enum import Enum
from pathlib import Path
from typing import Optional

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
        self._history = []
    
    def _get_last_action(self, trajectory: str) -> str:
        matches = re.findall(r"Action:.*", trajectory)
        if matches:
            return matches[-1]
        else:
            raise ValueError("Couldn't extract an Action")
    
    def inspect_history(self, n:Optional[int] = None) -> str:
        if not n:
            return str(self._history)
        else:
            return str(self._history[-n:])

    def __call__(self, userprompt: str, max_calls:int = 10) -> str:
        trajectory = ""
        for i in range(max_calls):
            if i == 0:
                trajectory = self.prompting_strategy(prompt=userprompt, begin=True)
            else:
                trajectory = self.prompting_strategy(prompt=trajectory, begin=False)

            self._history.append(trajectory)

            action_sequence = self._get_last_action(trajectory)
            obs = self.ACI.get_observation(action_sequence)
            trajectory += obs

            self._history.append(trajectory)

            if self.ACI.finished:
                break

        return trajectory
