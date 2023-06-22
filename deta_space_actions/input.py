from enum import Enum


class InputType(Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"


class Input:
    """Represents an input parameter to a Deta Space app action."""

    def __init__(self, name: str, type: InputType = InputType.STRING, optional: bool = False):
        self.name = name
        self.type = type
        self.optional = optional

    def to_dict(self):
        """Return a JSON-serializable representation of the input parameter."""
        return {
            "name": self.name,
            "type": self.type.value,
            "optional": self.optional,
        }
