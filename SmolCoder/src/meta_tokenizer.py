import re
from abc import ABC, abstractmethod
from typing import List, Tuple, Union

# Importing the necessary classes from the hypothetical external modules
from SmolCoder.src.prompting_strategy import PromptingStrategy
from SmolCoder.src.toolkit import Toolkit

# Constants for token keywords
QUESTION_PREFIX = "Question:"
THOUGHT_PREFIX = "Thought:"
ACTION_PREFIX = "Action:"
OBSERVATION_PREFIX = "Observation:"
FEWSHOT_PREFIX = "StartFewShotExamples"
FEWSHOT_SUFFIX = "EndFewShotExamples"

class MetaToken(ABC):
    @abstractmethod
    def match(cls, text: str) -> Union['MetaToken', None]:
        pass
    
    @abstractmethod
    def unparse(self) -> str:
        pass


class SysPrompt(MetaToken):
    def __init__(self, content: str) -> None:
        self.content = content

    @classmethod
    def match(cls, text: str) -> Union['SysPrompt', None]:
        # SysPrompt matching logic should be handled separately by the tokenizer since it relies on the prompting strategy
        return None

    def unparse(self) -> str:
        return self.content
    
    # used for debugging purpose
    def __str__(self):
        return "SysPromptToken"


class FewShotExamples(MetaToken):
    def __init__(self, content: str) -> None:
        self.content = content

    @classmethod
    def match(cls, text: str) -> Union['Thought', None]:
        pattern = rf"{FEWSHOT_PREFIX}(.*?){FEWSHOT_SUFFIX}"
        match = re.search(pattern, text, re.DOTALL) 

        print("the match is: " + str(match))
        print("the text is: \n" + str(text))
        
        if match:
            return cls(content=match.group(1).strip())
        return None

    def unparse(self) -> str:
        return f"{FEWSHOT_PREFIX} {self.content}{FEWSHOT_SUFFIX}"

    # used for debugging purpose
    def __str__(self):
        return "FewShotExampleToken"


class Question(MetaToken):
    def __init__(self, content: str) -> None:
        self.content = content

    @classmethod
    def match(cls, text: str) -> Union['Question', None]:
        if text.startswith(QUESTION_PREFIX):
            question_end = text.find(THOUGHT_PREFIX)
            if question_end != -1:
                content = text[len(QUESTION_PREFIX):question_end].strip()
            else:
                content = text[len(QUESTION_PREFIX):].strip()
            return cls(content)
        return None

    def unparse(self) -> str:
        return f"{QUESTION_PREFIX} {self.content}"
    
    # used for debugging purpose
    def __str__(self):
        return "QuestionToken"


class Thought(MetaToken):
    def __init__(self, content: str) -> None:
        self.content = content

    @classmethod
    def match(cls, text: str) -> Union['Thought', None]:
        match = re.match(rf"{THOUGHT_PREFIX} (.+?)(?=({ACTION_PREFIX}|$))", text, re.DOTALL)
        if match:
            return cls(content=match.group(1).strip())
        return None

    def unparse(self) -> str:
        return f"{THOUGHT_PREFIX} {self.content}"

    # used for debugging purpose
    def __str__(self):
        return "ThoughtToken"



class Action(MetaToken):
    def __init__(self, tool_name: str, input_variables: List[str]) -> None:
        self.tool_name = tool_name
        self.input_variables = input_variables

    def __eq__(self, other):
        if not isinstance(other, Action):
            return False
        return self.tool_name == other.tool_name and self.input_variables == other.input_variables

    @classmethod
    def match(cls, text: str) -> Union['Action', None]:
        match = re.match(rf"{ACTION_PREFIX} ([\w_]+)\[(.*?)\](?=({OBSERVATION_PREFIX}|$))", text, re.DOTALL)
        if match:
            tool_name = match.group(1).strip()
            input_variables = [var.strip() for var in match.group(2).strip().split(',')] if match.group(2).strip() else []
            return cls(tool_name=tool_name, input_variables=input_variables)
        return None

    def unparse(self) -> str:
        input_vars = ", ".join(self.input_variables)
        return f"{ACTION_PREFIX} {self.tool_name}[{input_vars}]"

    def unpack(self) -> Tuple[str, List[str]]:
        return self.tool_name, self.input_variables

    # used for debugging purpose
    def __str__(self):
        return "ActionToken"

#TODO: Observation should carry content and cwd. Cwd should only be printed in the last observation to save space 
class Observation(MetaToken):
    def __init__(self, content: str) -> None:
        self.content = content

    @classmethod
    def match(cls, text: str) -> Union['Observation', None]:
        match = re.match(rf"{OBSERVATION_PREFIX} (.+?)(?=({THOUGHT_PREFIX}|{ACTION_PREFIX}|$))", text, re.DOTALL)
        if match:
            return cls(content=match.group(1).strip())
        return None

    def unparse(self) -> str:
        return f"{OBSERVATION_PREFIX} {self.content}"

    # used for debugging purpose
    def __str__(self):
        return "ObservationToken"

class MetaTokenizer:
    
    def __init__(self, tool_kit: Toolkit, prompting_strategy: PromptingStrategy) -> None:
        self.sysprompt_token = self._get_sysprompt_token(prompting_strategy)
        self.possible_action_token_names = tool_kit.get_possible_actions()

    def _get_sysprompt_token(self, prompting_strategy: PromptingStrategy) -> SysPrompt:
        return SysPrompt(content=prompting_strategy.sysprompt) #TODO: this can be made much easier. Make Sysprompt into Parantheses [sys] [/sys] 

    def tokenize(self, trajectory: str) -> List[MetaToken]:
        token_stream = []

        # Match SysPrompt Token
        sys_prompt_length = len(self.sysprompt_token.content)
        expected_sysprompt = self.sysprompt_token.content
        if trajectory.startswith(expected_sysprompt):
            token_stream.append(self.sysprompt_token)
            trajectory = trajectory[sys_prompt_length:].strip()

        trajectory = trajectory.replace("\n", "")
        
        #Handles FewShotExamples in the prompt
        #token = FewShotExamples.match(trajectory)
        #token_stream.append(token)
        #trajectory = trajectory[len(token.unparse()):].strip()  
        
        while trajectory:
            for token_class in [Question, Thought, Action, Observation]:
                token = token_class.match(trajectory)
                if token:
                    token_stream.append(token)
                    trajectory = trajectory[len(token.unparse()):].strip()  # Adjusting the length accordingly
                    break
            else:
                break  # If no tokens match, exit the loop

        return token_stream
    
    def is_valid_traj(self, traj: Union[str, List[MetaToken]]) -> bool:
        if isinstance(traj, str):
            token_stream = self.tokenize(traj)
        else:
            token_stream = traj

        if not token_stream:
            print("Logger: when validatin the trajectory the trajectory was empty.")
            return False

        if not isinstance(token_stream[0], SysPrompt):
            print("Logger: when validating the trajectory, the first metatoken was not a systemprompt.")
            return False

        if len(token_stream) > 1 and not isinstance(token_stream[1], Question):
            print("Logger: when validating the trajectory, the second token was not a question token.")
            return False

        expected_types = [Thought, Action, Observation]
        index = 2
        while index < len(token_stream):
            expected_type = expected_types[(index - 2) % 3]
            if not isinstance(token_stream[index], expected_type):
                print("Logger: When validating the trajectory, a unexspected token was found: expected: '" + str(expected_type) + "' but got: '" + str(token_stream[index]) + "'.")
                
                token_str_test = "("
                for curr_token in token_stream:
                    token_str_test += str(curr_token) + ", "
                token_str_test += ")"
           
                print("Current token stream: " + str(token_str_test))
                return False
            index += 1

        return True

    def unparse(self, token_stream: List[MetaToken]) -> str:
        return "\n".join(token.unparse() for token in token_stream)
