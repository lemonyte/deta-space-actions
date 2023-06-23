from typing import Any, Awaitable, Callable, MutableMapping, Sequence

from starlette.exceptions import HTTPException
from starlette.requests import Request

from .input import Input

# TODO: MutableMapping is incompatible with Dict??
HandlerInput = MutableMapping[str, Any]
ActionHandler = Callable[[HandlerInput], Awaitable[Any]]
MISSING = Any


class Action:
    """Represents a Deta Space app action."""

    def __init__(
        self,
        name: str,
        handler: ActionHandler,
        base_path: str,
        inputs: Sequence[Input] = MISSING,
        title: str = "",
    ):
        self.name = name
        self.handler = handler
        self.inputs = inputs
        self.title = title
        self.path = f"{base_path}/{self.name}"

    def run(self, payload: HandlerInput):
        return self.handler(payload)


class Actions:
    """Represents a collection of Deta Space app actions."""

    declaration_path = "/__space/actions"

    def __init__(self, base_path: str = declaration_path):
        self.base_path = base_path
        self._actions: MutableMapping[str, Action] = {}

    def add(self, name: str, handler: ActionHandler, inputs: Sequence[Input] = MISSING, title: str = "") -> Action:
        """Add an action."""
        if name in self._actions:
            raise ValueError(f"action '{name}' already exists")
        action = Action(name, handler, self.base_path, inputs, title)
        self._actions[action.name] = action
        return action

    def declaration(self):
        """Return a JSON-serializable declaration of the actions and their inputs."""
        return {
            "actions": [
                {
                    "name": action.name,
                    "title": action.title,
                    "path": action.path,
                    "input": [input.to_dict() for input in action.inputs],
                }
                for action in self._actions.values()
            ],
        }

    async def middleware(self, request: Request, call_next):
        # TODO: make it generic asgi with no dependencies
        if request.method == "GET" and request.url.path == self.declaration_path:
            return self.declaration()
        if request.method == "POST" and request.url.path.startswith(self.base_path):
            name = request.url.path.lstrip(self.base_path + "/").rstrip("/")
            action = self._actions.get(name)
            if not action:
                raise HTTPException(404, f"Action {name} not found")
            return await action.run(await request.json())
        return await call_next(request)
