
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
        Note that the userprompt needs to start with "Question:"
        Also note that the __call__ method right now is tailored for ReAct.
        It might need to be adapted for other prompting strategies.
        """
        if start_cwd != "":
            self.ACI._change_cwd(start_cwd)

        
        if self.logger is not None:
            self.logger.info("Starting SmolCoder call with userprompt: %s, max_calls: %d", userprompt, max_calls)
        
        trajectory = ""
        last_action = None

        for i in range(max_calls):
            if self.logger:
                self.logger.debug("Call iteration: %d", i)
            if i == 0:
                trajectory = self.prompting_strategy(prompt=userprompt, begin=True)
            else:
                trajectory = self.prompting_strategy(prompt=trajectory, begin=False)
            

            if self.logger is not None:
                print("\n------------\n")
                print(trajectory)
                print("\n------------\n")

            self.token_stream = self.meta_tokenizer.tokenize(trajectory)
            assert self.meta_tokenizer.is_valid_traj(trajectory), f"{self.token_stream}"
            self._history.append(trajectory)

            # assert isinstance(self.token_stream[-1], Action)
            action: Action = self.token_stream[-1]
            

            # Debugging
            # ------------------------------------------------------------------
            token_str_test = "("
            for curr_token in self.token_stream:
                token_str_test += str(curr_token) + ", "
            token_str_test += ")"

            if self.logger is not None:
                self.logger.debug("\n-------")
                self.logger.debug("Current action_stream: " + token_str_test + "\n")
                self.logger.debug("Last token: " + str(action))
                self.logger.debug("-------\n")
            
            if self.logger is not None:
                if action == last_action:
                    self.logger.debug(f"\nThe Last Action is the same as current action: {str(action)}\n")
            # ------------------------------------------------------------------
            

            # This happens when the agent forgets to adhere to the ReAct framework
            # e.g. after the observation instead of generating something starting with "Action" it generates bullshit
            if not isinstance(self.token_stream[-1], Action):
                trajectory += """\n
It looks like the current response deviates from the expected sequence of Action, Thought, Observation. Please adhere to the following format to maintain consistency:
[Thought] Reasoning which action to take to solve the task.
[Action] Always either List_Files[folder] or Move_to_Folder[new_directory] or List_Classes[file_name] or List_Methods[class_name] or Show_Method_Body[class_name,method_name] or Replace_Method[class_name,method_name,new_method] or Finish[answer]
[Observation] result of the previous Action
[Thought] next steps to take based on the previous Observation
...
until Action is of type `Finish`.
Do not use any special formatation such as markdown.
"The 'Observation' will automatically returned to you after you used an action, you do not need to generate it.
\n
"""
                
                self._history.append(trajectory)
                continue

            
            # If we repeat an action, we backtrack
            if last_action and action == last_action:
                
                if self.logger is not None:
                    self.logger.warning("Detected repeated action. Attempting backtracking.")
                    print("Detected repeated action.")
                assert self._backtrack_action(), "Something went wrong while backtracking"
                trajectory = self.meta_tokenizer.unparse(self.token_stream)

            last_action = action
           
            # For debugging purpose, only           
            if isinstance(action, Action):
                if self.logger is not None:
                    self.logger.debug("------")
                    self.logger.debug("action: " + str(action.tool_name))

                    self.logger.debug("action args: " + str(action.input_variables))
                    self.logger.debug("------")
                    

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

            assert self.meta_tokenizer.is_valid_traj(trajectory), f"{self.token_stream}"
            self.token_stream = self.meta_tokenizer.tokenize(trajectory)

            self._history.append(trajectory)

            if self.ACI.finished:
                break
        
        if self.logger is not None:
            self.logger.info("Final trajectory: %s", trajectory)
        return trajectory
