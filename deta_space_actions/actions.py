import json
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    MutableMapping,
    Optional,
    Sequence,
)

from .input import Input

if TYPE_CHECKING:
    from asgiref.typing import (
        ASGI3Application,
        ASGIReceiveCallable,
        ASGISendCallable,
        Scope,
    )

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

    def get(self, name: str) -> Optional[Action]:
        """Get an action by name."""
        return self._actions.get(name)

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


class ActionsMiddleware:
    def __init__(self, app: "ASGI3Application", actions: Actions):
        self.app = app
        self.actions = actions

    async def __call__(self, scope: "Scope", receive: "ASGIReceiveCallable", send: "ASGISendCallable"):
        if scope["type"] == "http":
            if scope["path"].rstrip("/") == self.actions.declaration_path:
                if scope["method"] != "GET":
                    await self.send_plain_text(send, "Method Not Allowed", status=405)
                    return
                await self.send_json(send, self.actions.declaration())
                return
            if scope["path"].startswith(self.actions.base_path):
                if scope["method"] != "POST":
                    await self.send_plain_text(send, "Method Not Allowed", status=405)
                    return
                name = scope["path"].lstrip(self.actions.base_path + "/").rstrip("/")
                action = self.actions.get(name)
                if not action:
                    await self.send_plain_text(send, "Not Found", status=404)
                    return
                message = await receive()
                if message["type"] == "http.request":
                    payload = json.loads(message["body"])
                    await self.send_json(send, await action.run(payload))
                    return
        await self.app(scope, receive, send)

    async def send_plain_text(self, send: "ASGISendCallable", content: str, status: int = 200):
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [(b"Content-Type", b"text/plain; charset=utf-8")],
                "trailers": False,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": content.encode("utf-8"),
                "more_body": False,
            }
        )

    async def send_json(self, send: "ASGISendCallable", content: Any, status: int = 200):
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [(b"Content-Type", b"application/json")],
                "trailers": False,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": json.dumps(
                    content,
                    ensure_ascii=False,
                    allow_nan=False,
                    indent=None,
                    separators=(",", ":"),
                ).encode("utf-8"),
                "more_body": False,
            }
        )
