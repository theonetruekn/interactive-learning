import logging

from pathlib import Path
from typing import List 

import re
from typing import Optional

from SmolCoder.src.prompting_strategy import PromptingStrategy
from SmolCoder.src.aci import AgentComputerInterface
from SmolCoder.src.llm_wrapper import LLM
from SmolCoder.src.toolkit import Toolkit


log_file = Path('smolcoder.log')
logging.basicConfig(filename=log_file, filemode='a', level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


class SmolCoder:
    """
    This class handles the communication between the prompting strategy and the agent-computer-interface.
    """
    def __init__(self, model:LLM, codebase_dir:Path, toolkit:Toolkit, prompting_strategy:str = "ReAct") -> None:
        self.ACI = AgentComputerInterface(cwd=codebase_dir, tools=toolkit)
        self.prompting_strategy = PromptingStrategy.create(model, strategy=prompting_strategy, toolkit=toolkit)
        self._history = []

        logger.debug("SmolCoder initialized with model: %s, codebase_dir: %s, toolkit: %s, prompting_strategy: %s",
                     model, codebase_dir, toolkit, prompting_strategy)
    
    def _get_last_action(self, trajectory: str) -> str:
        matches = re.findall(r"Action:.*", trajectory)
        if matches:
            last_action = matches[-1]
            logger.debug("Extracted last action: %s", last_action)
            return last_action
        else:
            logger.error("Couldn't extract an Action from trajectory: %s", trajectory)
            raise ValueError("Couldn't extract an Action")
    
    def inspect_history(self, n:Optional[int] = None) -> str:
        if not n:
            return self._format_history(self._history)
        else:
            return self._format_history(self._history[-n:])
    
    def _format_history(self, history_input: List[str]) -> str:
        result = ""
        for item in history_input:
            result += item 

        return result 

    def __call__(self, userprompt: str, max_calls:int = 10) -> str:
        logger.info("Starting SmolCoder call with userprompt: %s, max_calls: %d", userprompt, max_calls)
        trajectory = ""
        for i in range(max_calls):
            logger.debug("Call iteration: %d", i)
            if i == 0:
                trajectory = self.prompting_strategy(prompt=userprompt, begin=True)
            else:
                trajectory = self.prompting_strategy(prompt=trajectory, begin=False)

            self._history.append(trajectory)

            try:
                action_sequence = self._get_last_action(trajectory)
                obs, cwd_msg = self.ACI.get_observation(action_sequence)
                trajectory += obs + cwd_msg 

                self._history.append(trajectory)

                if self.ACI.finished:
                    return obs

            except Exception as e:
                logger.exception("Exception occurred during SmolCoder call: %s", e)
                raise

        logger.info("Final trajectory: %s", trajectory)
        return trajectory
