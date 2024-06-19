import re
import difflib

from abc import ABC
from typing import List, Union

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

        # Match SysPrompt Token
        sys_prompt_length = len(self.sysprompt_token.content)
        expected_sysprompt = self.sysprompt_token.content
        if trajectory.startswith(expected_sysprompt):
            token_stream.append(self.sysprompt_token)
            trajectory = trajectory[sys_prompt_length:].strip()

        # Match Question token
        if trajectory.startswith("Question:"):
            question_end = trajectory.find("Thought:")
            if question_end != -1:
                question_content = trajectory[len("Question:"):question_end].strip()
                token_stream.append(Question(content=question_content))
                trajectory = trajectory[question_end:].strip()
            else:
                question_content = trajectory[len("Question:"):].strip()
                token_stream.append(Question(content=question_content))
                return token_stream

        # Patterns for matching Thought, Action, and Observation tokens
        thought_pattern = re.compile(r"Thought: (.+?)(?=(Action:|Observation:|Thought:|$))", re.DOTALL)
        action_pattern = re.compile(r"Action: ([\w_]+\[(.*?)\])(?=(Observation:|Thought:|Action:|$))", re.DOTALL)
        observation_pattern = re.compile(r"Observation: (.+?)(?=(Thought:|Action:|Observation:|$))", re.DOTALL)

        # Loop to match Thought, Action, and Observation tokens
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
    
    def is_valid_traj(self, traj: Union[str, List[MetaToken]]) -> bool:
        if isinstance(traj, str):
            token_stream = self.tokenize(traj)
        else:
            token_stream = traj

        if not token_stream:
            return False

        if not isinstance(token_stream[0], SysPrompt):
            return False

        if len(token_stream) < 2 or not isinstance(token_stream[1], Question):
            return False

        index = 2
        while index < len(token_stream):
            if index >= len(token_stream) or not isinstance(token_stream[index], Thought):
                return False
            index += 1

            if index >= len(token_stream) or not isinstance(token_stream[index], Action):
                return False
            index += 1

            if index >= len(token_stream) or not isinstance(token_stream[index], Observations):
                return False
            index += 1

        return True

    def unparse(self, token_stream: List[MetaToken]) -> str:
        if not token_stream:
            return ""
        
        trajectory = []
        initial_content = []

        for token in token_stream:
            if isinstance(token, SysPrompt):
                initial_content.append(token.content)
            elif isinstance(token, Question):
                initial_content.append(token.content)
            else:
                break

        trajectory.append(" ".join(initial_content))

        for token in token_stream[len(initial_content):]:
            if isinstance(token, Thought):
                trajectory.append(f"Thought: {token.content}")
            elif isinstance(token, Action):
                input_vars = ", ".join(token.input_variables)
                trajectory.append(f"Action: {token.tool_name}[{input_vars}]")
            elif isinstance(token, Observations):
                trajectory.append(f"Observation: {token.content}")

        return "\n".join(trajectory)