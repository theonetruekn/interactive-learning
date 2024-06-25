import logging

from pathlib import Path
from typing import List 

import re
from typing import Optional

from SmolCoder.src.prompting_strategy import PromptingStrategy
from SmolCoder.src.aci import AgentComputerInterface
from SmolCoder.src.llm_wrapper import LLM
from SmolCoder.src.toolkit import Toolkit


class SmolCoder:
    """
    This class handles the communication between the prompting strategy and the agent-computer-interface.
    """
    def __init__(self, model:LLM, codebase_dir:Path, toolkit:Toolkit, prompting_strategy:str = "ReAct", mode:int = 2) -> None:
        """
        Args:
            mode (int): 0 for github_issue_mode, 1 for repoduce_error_mode, 2 for ReAct Mode
        """
        log_file = Path('smolcoder.log')
        logging.basicConfig(filename=log_file, filemode='a', level=logging.DEBUG,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        self.ACI = AgentComputerInterface(cwd=codebase_dir, tools=toolkit, logger=self.logger)
        self.prompting_strategy = PromptingStrategy.create(model, 
                                                           strategy=prompting_strategy, 
                                                           toolkit=toolkit, 
                                                           mode=mode
                                                           )
        self._history = []

        self.logger.debug("-------------------------------------------------------------------------------------------")
        self.logger.debug("SmolCoder initialized with model: %s, codebase_dir: %s, toolkit: %s, prompting_strategy: %s",
                     model, codebase_dir, toolkit, prompting_strategy)
    
    def _get_last_action(self, trajectory: str) -> str:
        matches = re.findall(r"Action:.*", trajectory)
        if matches:
            last_action = matches[-1]
            self.logger.debug("Extracted last action: %s", last_action)
            return last_action
        else:
            self.logger.error("Couldn't extract an Action from trajectory: %s", trajectory)
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

    def __call__(self, userprompt: str, max_calls:int = 10, start_cwd: str = "") -> str:
        if start_cwd != "":
            self.ACI._change_cwd(start_cwd)

        self.logger.info("Starting SmolCoder call with userprompt: %s, max_calls: %d", userprompt, max_calls)
        trajectory = ""
        for i in range(max_calls):
            self.logger.debug("Call iteration: %d", i)
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
                self.logger.exception("Exception occurred during SmolCoder call: %s", e)
                raise

        self.logger.info("Final trajectory: %s", trajectory)
        return trajectory
