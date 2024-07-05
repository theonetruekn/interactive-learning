from abc import ABC, abstractmethod
from typing import Any, List

class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def input_variables(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def desc(self) -> str:
        pass

    @property
    @abstractmethod
    def example(self) -> str:
        pass
    
    @property
    def short_desc(self) -> str:
        return f'{self.name}[{",".join(self.input_variables)}]'
    
    def valid_params(self, input_variables) -> bool:
        return len(self.input_variables) == len(input_variables)

    def number_of_input_variables(self) -> int:
        return len(self.input_variables)
    
    @abstractmethod
    def __call__(self, input_variables:List[str], *args: Any, **kwds: Any) -> str:
        pass