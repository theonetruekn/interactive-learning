import logging

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
    def __init__(self, model:LLM, codebase_dir:Path, toolkit:Toolkit, prompting_strategy:str = "ReAct", mode:int = 2) -> None:
        if prompting_strategy != "ReAct":
            raise NotImplementedError("Currently, only 'ReAct' is a valid answer.")
        
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
        self.meta_tokenizer = MetaTokenizer(toolkit, self.prompting_strategy)
        self.token_stream: List[MetaToken] = [] # this saves the tokens (Action, Thought, Observation, ...)
        self._history = [] # this saves the history of the trajectory

        self.logger.debug("-------------------------------------------------------------------------------------------")
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
        Note that the userprompt needs to start with "Question:"
        Also note that the __call__ method right now is tailored for ReAct.
        It might need to be adapted for other prompting strategies.
        """
        if start_cwd != "":
            self.ACI._change_cwd(start_cwd)

        self.logger.info("Starting SmolCoder call with userprompt: %s, max_calls: %d", userprompt, max_calls)
        trajectory = ""
        last_action = None

        for i in range(max_calls):
            self.logger.debug("Call iteration: %d", i)
            if i == 0:
                trajectory = self.prompting_strategy(prompt=userprompt, begin=True)
            else:
                trajectory = self.prompting_strategy(prompt=trajectory, begin=False)

            print("\n------------\n")
            print(trajectory)
            print("\n------------\n")

            self.token_stream = self.meta_tokenizer.tokenize(trajectory)
            assert self.meta_tokenizer.is_valid_traj(trajectory), f"{self.token_stream}"
            self._history.append(trajectory)

            # assert isinstance(self.token_stream[-1], Action)
            action: Action = self.token_stream[-1]

            print("\nLast Action is the same as current action?: ", action == last_action, "\n")

            # If we repeat an action, we backtrack
            if last_action and action == last_action:
                self.logger.warning("Detected repeated action. Attempting backtracking.")
                print("Detected repeated action.")
                assert self._backtrack_action(), "Something went wrong while backtracking"
                trajectory = self.meta_tokenizer.unparse(self.token_stream)

            last_action = action
           
            if isinstance(action, Action):
                print("------")
                print("action: " + str(action.tool_name))

                print("action args: " + str(action.input_variables))
                print("------")
                

            tool_name, input_variables = action.unpack()
            # If the tool-use fails, we backtrack
            # FIXME: We might want to return errors?
            #try:
            obs = self.ACI.get_observation(tool_name=tool_name, input_variables=input_variables)
            #except Exception as e:
            #    self.logger.error(f"Error during observation: {str(e)}. Attempting backtracking.")
            #    print(f"Error during observation: {str(e)}. Attempting backtracking.")
            #    assert self._backtrack_action()
            #    continue
            trajectory += obs

            print("\n------------\n")
            print(trajectory)
            print("\n------------\n")

            assert self.meta_tokenizer.is_valid_traj(trajectory), f"{self.token_stream}"
            self.token_stream = self.meta_tokenizer.tokenize(trajectory)

            self._history.append(trajectory)

            if self.ACI.finished:
                break

        self.logger.info("Final trajectory: %s", trajectory)
        return trajectory
