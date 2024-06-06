# Basically ReAct with some tools, connected to pipeline 
from SmolCoder.src.aci import AgentComputerInterface

class SmolCoder:

    def __init__(self, agent_framework, ACI:AgentComputerInterface) -> None:
        # ReAct in our case
        self.agent_framework = agent_framework
        self.ACI = ACI