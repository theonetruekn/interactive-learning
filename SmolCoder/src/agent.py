import logging

from pathlib import Path

from SmolCoder.src.meta_tokenizer import Action, MetaToken, MetaTokenizer, Observation

log_file = Path('smolcoder.log')
logging.basicConfig(filename=log_file, filemode='a', level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

from typing import List, Optional

from SmolCoder.src.prompting_strategy import PromptingStrategy
from SmolCoder.src.aci import AgentComputerInterface
from SmolCoder.src.llm_wrapper import LLM
from SmolCoder.src.toolkit import Toolkit

class SmolCoder:
    """
    This class handles the communication between the prompting strategy and the agent-computer-interface.
    """
    def __init__(self, model:LLM, codebase_dir:Path, toolkit:Toolkit, prompting_strategy:str = "ReAct") -> None:
        if prompting_strategy != "ReAct":
            raise NotImplementedError("Currently, only 'ReAct' is a valid answer.")
        
        self.ACI = AgentComputerInterface(cwd=codebase_dir, tools=toolkit)
        self.prompting_strategy = PromptingStrategy.create(model, strategy=prompting_strategy, toolkit=toolkit)
        self.meta_tokenizer = MetaTokenizer(toolkit, self.prompting_strategy)
        self.token_stream: List[MetaToken] = [] # this saves the tokens (Action, Thought, Observation, ...)
        self._history = [] # this saves the history of the trajectory

        logger.debug("SmolCoder initialized with model: %s, codebase_dir: %s, toolkit: %s, prompting_strategy: %s",
                     model, codebase_dir, toolkit, prompting_strategy)
    
    def inspect_history(self, n:Optional[int] = None) -> str:
        if not n:
            return str(self._history)
        else:
            return str(self._history[-n:])

    def __call__(self, userprompt: str, max_calls:int = 10) -> str:
        """
        Note that the userprompt needs to start with "Question:"
        Also note that the __call__ method right now is tailored for ReAct.
        It might need to be adapted for other prompting strategies.
        """
        logger.info("Starting SmolCoder call with userprompt: %s, max_calls: %d", userprompt, max_calls)
        trajectory = ""
        for i in range(max_calls):
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
            
            action = self.token_stream[-1]
            # check if last token is Action
            assert isinstance(action, Action)
            tool_name, input_variables = action.unpack()
            
            obs = self.ACI.get_observation(tool_name=tool_name, input_variables=input_variables)
            trajectory += obs
            
            print("\n------------\n")
            print(trajectory)
            print("\n------------\n")

            assert self.meta_tokenizer.is_valid_traj(trajectory), f"{self.token_stream}"
            self.token_stream = self.meta_tokenizer.tokenize(trajectory)
            assert isinstance(self.token_stream[-1], Observation)

            self._history.append(trajectory)

            if self.ACI.finished:
                break
            

        logger.info("Final trajectory: %s", trajectory)
        return trajectory
