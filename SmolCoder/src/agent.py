from SmolCoder.src.prompting_strategy import PromptingStrategy
from SmolCoder.src.aci import AgentComputerInterface
from SmolCoder.src.llm_wrapper import LLM

class SmolCoder:
    """
    This class handles the communication between the prompting strategy and the agent-computer-interface.
    """
    def __init__(self, model:LLM, ACI:AgentComputerInterface, prompting_strategy:str = "ReAct") -> None:
        self.prompting_strategy = PromptingStrategy.create(model, strategy=prompting_strategy)
        self.ACI = ACI
    
    def __call__(self, userprompt: str) -> str:
        # interaction between ACI and prompting_strategy
        raise NotImplementedError