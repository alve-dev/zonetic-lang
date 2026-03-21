from dataclasses import dataclass
from typing import Any

@dataclass
class RuntimeValue:
    value: Any

class RuntimeScope:
    def __init__(self, parent=None):
        self.values: dict[str, RuntimeValue] = {}
        self.parent = parent
    
    def get(self, name: str) -> RuntimeValue | None:
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        return None
    
    def set(self, name: str, value: RuntimeValue) -> None:
        self.values[name] = value
    
    def update(self, name: str, value: Any) -> None:
        if name in self.values:
            self.values[name].value = value
        elif self.parent:
            self.parent.update(name, value)