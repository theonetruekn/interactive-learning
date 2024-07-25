import re
from abc import ABC, abstractmethod
from typing import List, Tuple, Union

from SmolCoder.src.toolkit import Toolkit

# Constants for token keywords
SYSPROMPT_TOKEN = "[Sysprompt]"
QUESTION_TOKEN = "[Question]"
THOUGHT_TOKEN = "[Thought]"
ACTION_TOKEN = "[Action]"
OBS_TOKEN = "[Observation]"

class MetaToken(ABC):
    @abstractmethod
    def match(cls, text: str) -> Tuple[Union['MetaToken', None], int]:
        pass
    
    @abstractmethod
    def unparse(self) -> str:
        pass


class SysPrompt(MetaToken):
    def __init__(self, content: str) -> None:
        self.content = content

    @classmethod
    def match(cls, text: str) -> Tuple[Union['SysPrompt', None], int]:
        pattern = re.escape(SYSPROMPT_TOKEN) + r"(.*?)" + re.escape(SYSPROMPT_TOKEN)
        match = re.match(pattern, text, re.DOTALL)
        if match:
            content = match.group(1)
            return cls(content), match.end()
        return None, -1

    def unparse(self) -> str:
        return f"{SYSPROMPT_TOKEN}{self.content}{SYSPROMPT_TOKEN}"
    
    # used for debugging purpose
    def __str__(self):
        return "SysPromptToken"


class Question(MetaToken):
    def __init__(self, content: str) -> None:
        self.content = content

    @classmethod
    def match(cls, text: str) -> Tuple[Union['Question', None], int]:
        pattern = re.escape(QUESTION_TOKEN) + r"(.*?)(?=" + r"|".join([
            re.escape(SYSPROMPT_TOKEN),
            re.escape(THOUGHT_TOKEN),
            re.escape(ACTION_TOKEN),
            re.escape(OBS_TOKEN),
            r"$"
        ]) + r")"
        match = re.match(pattern, text, re.DOTALL)
        if match:
            content = match.group(1)
            return cls(content), match.end()
        return None, -1

    def unparse(self) -> str:
        return f"{QUESTION_TOKEN}{self.content}"
    
    # used for debugging purpose
    def __str__(self):
        return "QuestionToken"


class Thought(MetaToken):
    def __init__(self, content: str) -> None:
        self.content = content

    @classmethod
    def match(cls, text: str) -> Tuple[Union['Thought', None], int]:
        text = text.strip()
        match = re.match(rf"{re.escape(THOUGHT_TOKEN)}(.+?)(?={re.escape(ACTION_TOKEN)}|$)", text, re.DOTALL)
        if match:
            content = match.group(1).strip()
            pointer = match.end()
            return cls(content=content), pointer
        return None, -1

    def unparse(self) -> str:
        return f"{THOUGHT_TOKEN}{self.content}"

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
    def match(cls, text: str) -> Tuple[Union['Action', None], int]:
        match = re.match(rf"{re.escape(ACTION_TOKEN)}\s*([\w_]+)\[(.*?)\](?={re.escape(OBS_TOKEN)}|$)", text, re.DOTALL)
        if match:
            tool_name = match.group(1)
            if tool_name == "Finish":
                input_variables = [match.group(2)]
            else:
                input_variables = [var.strip() for var in match.group(2).strip().split(',')] if match.group(2).strip() else []
            pointer = match.end()
            return cls(tool_name=tool_name, input_variables=input_variables), pointer
        return None, -1

    def unparse(self) -> str:
        if self.tool_name == "Finish":
            return f"{ACTION_TOKEN}{self.tool_name}[{self.input_variables[0]}]"
        input_vars = ", ".join(self.input_variables)
        return f"{ACTION_TOKEN}{self.tool_name}[{input_vars}]"

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
        match = re.match(rf"{re.escape(OBS_TOKEN)}(.+?)(?={re.escape(THOUGHT_TOKEN)}|{re.escape(ACTION_TOKEN)}|$)", text, re.DOTALL)
        if match:
            content = match.group(1).strip()
            pointer = match.end()
            return cls(content=content), pointer
        return None, -1

    def unparse(self) -> str:
        return f"{OBS_TOKEN}{self.content}"

    # used for debugging purpose
    def __str__(self):
        return "ObservationToken"


class MetaTokenizer:
    
    def __init__(self, tool_kit: Toolkit) -> None:
        self.possible_action_token_names = tool_kit.get_possible_actions()

    def tokenize(self, trajectory: str) -> List[MetaToken]:
        token_stream = []

        # Handle sysprompt token separately
        sys_prompt_token, pointer = SysPrompt.match(trajectory)
        if sys_prompt_token:
            token_stream.append(sys_prompt_token)
            trajectory = trajectory[pointer:]

        # normalize trajectory
        trajectory = trajectory.replace("\n", "")
        
        #Handles FewShotExamples in the prompt
        #token = FewShotExamples.match(trajectory)
        #token_stream.append(token)
        #trajectory = trajectory[len(token.unparse()):].strip()  
        
        while trajectory:
            trajectory = trajectory.strip()
            for token_class in [Question, Thought, Action, Observation]:
                token, pointer = token_class.match(trajectory)
                if token:
                    token_stream.append(token)
                    trajectory = trajectory[pointer:].strip()
                    break
            else:
                break

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
