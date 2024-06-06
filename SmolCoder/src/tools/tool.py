from abc import ABC, ABCMeta

class CombinedMeta(ABCMeta):
    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct)
        
        # Check for required static attributes
        required_static_attrs = ['name', 'input_variable', 'desc']
        for attr in required_static_attrs:
            if not isinstance(getattr(cls, attr, None), str):
                raise TypeError(f"Class '{name}' must define a static attribute '{attr}' as a string.")
        
        return cls

class Tool(ABC, metaclass=CombinedMeta):
   def __init__(self) -> None:
       super().__init__() 