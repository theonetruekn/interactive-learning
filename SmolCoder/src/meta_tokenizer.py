import re
import difflib

from abc import ABC
from typing import List

from SmolCoder.src.prompting_strategy import PromptingStrategy
from SmolCoder.src.toolkit import Toolkit

class MetaToken(ABC):
    pass

class SysPrompt(MetaToken):
    def __init__(self, content:str) -> None:
        self.content = content

class Question(MetaToken):
    def __init__(self, content:str) -> None:
        self.content = content

class Thought(MetaToken):
    def __init__(self, content) -> None:
        self.content = content

class Action(MetaToken):
    def __init__(self, tool_name:str, input_variables:List[str]) -> None:
        self.tool_name = tool_name
        self.input_variables = input_variables

    def __eq__(self, other):
        if not isinstance(other, Action):
            return False
        return self.tool_name == other.tool_name and self.input_variables == other.input_variables

class Observations(MetaToken):
    def __init__(self, content) -> None:
        self.content = content

class MetaTokenizer:
    
    def __init__(self, tool_kit:Toolkit, prompting_strategy:PromptingStrategy) -> None:
        self.sysprompt_token = self._get_sysprompt_token(prompting_strategy)
        self.possible_action_token_names = tool_kit.get_possible_actions()

    def _get_sysprompt_token(self, prompting_strategy:PromptingStrategy) -> SysPrompt:
        return SysPrompt(content=prompting_strategy.sysprompt)

    def tokenize(self, trajectory: str) -> List[MetaToken]:
        token_stream = []

        sys_prompt_length = len(self.sysprompt_token.content)
        expected_sysprompt = self.sysprompt_token.content
        actual_sysprompt = trajectory[:sys_prompt_length]
        if not trajectory.startswith(expected_sysprompt):
            diff = '\n'.join(difflib.unified_diff(
                expected_sysprompt.splitlines(), 
                actual_sysprompt.splitlines(),
                fromfile='expected', 
                tofile='actual',
                lineterm=''
            ))
            raise ValueError(f"Trajectory does not start with the expected SysPrompt content. Difference:\n{diff}")

        token_stream.append(self.sysprompt_token)
        trajectory = trajectory[sys_prompt_length:].strip()

        thought_start = trajectory.find("Thought:")
        if thought_start == -1:
            raise ValueError("Trajectory must contain a Thought token after Question.")
        question_content = trajectory[:thought_start].strip()
        if question_content.startswith("Question:"):
            question_content = question_content[len("Question:"):].strip()
        token_stream.append(Question(content=question_content))
        trajectory = trajectory[thought_start:].strip()

        thought_pattern = re.compile(r"Thought: (.+?)(?=Action:|$)", re.DOTALL)
        action_pattern = re.compile(r"Action: ([\w_]+\[(.*?)\])(?=\nObservation:|$)", re.DOTALL)
        observation_pattern = re.compile(r"Observation: (.+?)(?=Thought:|$)", re.DOTALL)

        while trajectory:
            if trajectory.startswith("Thought:"):
                match = thought_pattern.match(trajectory)
                if match:
                    token_stream.append(Thought(content=match.group(1).strip()))
                    trajectory = trajectory[match.end():].strip()
                else:
                    break
            elif trajectory.startswith("Action:"):
                match = action_pattern.match(trajectory)
                if match:
                    tool_name = match.group(1).strip()
                    arguments = match.group(2).strip()
                    
                    if arguments:
                        input_variables = [var.strip() for var in arguments.split(',')]
                    else:
                        input_variables = []
                    
                    token_stream.append(Action(tool_name=tool_name, input_variables=input_variables))
                    trajectory = trajectory[match.end():].strip()
                else:
                    break
            elif trajectory.startswith("Observation:"):
                match = observation_pattern.match(trajectory)
                if match:
                    token_stream.append(Observations(content=match.group(1).strip()))
                    trajectory = trajectory[match.end():].strip()
                else:
                    break
            else:
                break

        return token_stream