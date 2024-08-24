
from os import execv
from pathlib import Path

from SmolCoder.src.meta_tokenizer import Action, MetaToken, MetaTokenizer, Observation
from typing import List 

from typing import List, Optional

from SmolCoder.src.prompting_strategy import PromptingStrategy
from SmolCoder.src.aci import AgentComputerInterface
from SmolCoder.src.llm_wrapper import LLM
from SmolCoder.src.toolkit import Toolkit


class SmolCoder:
    """
    This class handles the communication between the prompting strategy and the agent-computer-interface.
    """
    def __init__(self, model:LLM, codebase_dir:Path, toolkit:Toolkit, logger, prompting_strategy:str = "ReAct", mode:int = 2) -> None:
        if prompting_strategy != "ReAct":
            raise NotImplementedError("Currently, only 'ReAct' is a valid answer.")
        
        """
        Args:
            mode (int): 0 for github_issue_mode, 1 for repoduce_error_mode, 2 for ReAct Mode
        """
        self.logger = logger
        self.ACI = AgentComputerInterface(cwd=codebase_dir, tools=toolkit, logger=self.logger)
        self.prompting_strategy = PromptingStrategy.create(model, 
                                                           strategy=prompting_strategy, 
                                                           toolkit=toolkit, 
                                                           mode=mode
                                                           )
        self.meta_tokenizer = MetaTokenizer(toolkit)
        self.token_stream: List[MetaToken] = [] # this saves the tokens (Action, Thought, Observation, ...)
        self._history = [] # this saves the history of the trajectory
        
        if self.logger is not None:
            self.logger.debug("-------------------------------------------------------------------------------------------")
            self.logger.debug("-------------------------------------------------------------------------------------------")
            self.logger.debug("Started new SmolCoder Run")
            self.logger.debug("SmolCoder initialized with model: %s, codebase_dir: %s, toolkit: %s, prompting_strategy: %s",
                         model, codebase_dir, toolkit, prompting_strategy)
    
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

    def _backtrack_action(self) -> bool:
        if isinstance(self.token_stream[-1], Action):
            self.token_stream.pop()
            return True
        return False

    def __call__(self, userprompt: str, max_calls: int = 10, start_cwd: str = "") -> str:
        """
        Note that the userprompt needs to start with "[Question]"
        Also note that the __call__ method right now is tailored for ReAct.
        It might need to be adapted for other prompting strategies.
        """
        if start_cwd != "":
            self.ACI._change_cwd(start_cwd)
        
        if self.logger is not None:
            self.logger.info("Starting SmolCoder call with userprompt: %s, max_calls: %d", userprompt, max_calls)
        
        trajectory = ""

        for i in range(max_calls):
            temp_traj = trajectory
            temp_token_stream = self.token_stream
            if self.logger:
                self.logger.info("Call iteration: %d", i)
            if i == 0:
                temp_traj = self.prompting_strategy(prompt=userprompt, begin=True)
            else:
                temp_traj = self.prompting_strategy(prompt=temp_traj, begin=False)
            
            if self.logger is not None:
                self.logger.info(f"Current call trajectory:\n{temp_traj}")

            temp_token_stream = self.meta_tokenizer.tokenize(temp_traj)
            if not self.meta_tokenizer.is_valid_traj(temp_traj):
                if self.logger:
                    self.logger.info("Early error. Backtracking.")
                continue

            if not isinstance(temp_token_stream[-1], Action):
                if self.logger:
                    self.logger.info("Action format invalid. Backtracking")
                continue
            action: Action = temp_token_stream[-1]

            # Debugging
            # ------------------------------------------------------------------
            token_str_test = "("
            for curr_token in temp_token_stream:
                token_str_test += str(curr_token) + ", "
            token_str_test += ")"
            
            if isinstance(action, Action):
                if self.logger:
                    self.logger.debug("------")
                    self.logger.debug("action: " + str(action.tool_name))

                    self.logger.debug("action args: " + str(action.input_variables))
                    self.logger.debug("------")
            # ------------------------------------------------------------------      

            tool_name, input_variables = action.unpack()
            obs = self.ACI.get_observation(tool_name=tool_name, input_variables=input_variables)
            temp_traj += obs

            if self.logger is not None:
                self.logger.info(f"Current call trajectory:\n{temp_traj}")

            if not self.meta_tokenizer.is_valid_traj(temp_traj):
                if self.logger:
                    self.logger.info("Trajectory invalid after Observation. Backtracking.")
                continue
            temp_token_stream = self.meta_tokenizer.tokenize(temp_traj)

            # After successful looping, update agent state
            self.token_stream = temp_token_stream
            trajectory = temp_traj
            self._history.append(trajectory) #TODO: Make graph

            if self.ACI.finished:
                if self.logger is not None:
                    self.logger.info("Finished before expiration!")
                break
        
        if self.logger is not None:
            self.logger.info("Final trajectory: %s", trajectory)
        
        return trajectory
