import json
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Iterable,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    Type,
)

from .input import Input
from .view import RawView, View

if TYPE_CHECKING:
    from asgiref.typing import (
        ASGI3Application,
        ASGIReceiveCallable,
        ASGISendCallable,
        Scope,
    )

# TODO: MutableMapping is incompatible with Dict??
HandlerInput = MutableMapping[str, Any]
ActionHandler = Callable[[HandlerInput], Awaitable[View]]


class Action:
    """Represents a Deta Space app action."""

    def __init__(
        self,
        handler: ActionHandler,
        *,
        base_path: str,
        name: str = "",
        title: str = "",
        inputs: Sequence[Input] = tuple(),
        view: Type[View] = RawView,
    ):
        self.handler = handler
        self.name = name or handler.__name__
        self.title = title
        self.inputs = inputs
        self.view = view
        self.path = f"{base_path}/{self.name}"

    def __call__(self, payload: HandlerInput):
        """Run the action with the provided payload."""
        return self.handler(payload)


class Actions:
    """Represents a collection of Deta Space app actions."""

    declaration_path = "/__space/actions"

    def __init__(self, base_path: str = declaration_path):
        self.base_path = base_path
        self._actions: MutableMapping[str, Action] = {}

    def add(
        self,
        handler: ActionHandler,
        *,
        name: str = "",
        title: str = "",
        inputs: Sequence[Input] = tuple(),
        view: Type[View] = RawView,
    ) -> Action:
        """Add an action."""
        name = name or handler.__name__
        if name in self._actions:
            raise ValueError(f"action '{name}' already exists")
        action = Action(
            handler=handler,
            base_path=self.base_path,
            name=name,
            title=title,
            inputs=inputs,
            # TODO: get view type from handler return type hint.
            view=view,
        )
        self._actions[action.name] = action
        return action

    def get(self, name: str) -> Optional[Action]:
        """Get an action by name."""
        return self._actions.get(name)

    def action(
        self,
        *,
        name: str = "",
        title: str = "",
        inputs: Sequence[Input] = tuple(),
        view: Type[View] = RawView,
    ):
        """Decorator to add an action."""

        def decorator(handler: ActionHandler):
            return self.add(
                handler=handler,
                name=name,
                title=title,
                inputs=inputs,
                view=view,
            )

        return decorator

    def as_serializable(self):
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
    def __init__(self, app: "ASGI3Application", actions: Actions, decoder: Optional[Type[json.JSONDecoder]] = None):
        self.app = app
        self.actions = actions
        self.decoder = decoder

    async def __call__(self, scope: "Scope", receive: "ASGIReceiveCallable", send: "ASGISendCallable"):
        if scope["type"] == "http":
            if scope["path"].rstrip("/") == self.actions.declaration_path:
                if scope["method"] != "GET":
                    await self.send_plain_text(send, "Method Not Allowed", status=405)
                    return
                await self.send_json(send, self.actions.as_serializable())
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
                    try:
                        payload = json.loads(message["body"], cls=self.decoder)
                    except json.JSONDecodeError:
                        payload = {}
                    output = await action(payload)
                    try:
                        await self.send_json(send, output)
                    except TypeError:
                        await self.send_plain_text(send, str(output))
                    return
        await self.app(scope, receive, send)

    async def send(
        self,
        send: "ASGISendCallable",
        body: bytes,
        *,
        status: int = 200,
        headers: Iterable[Tuple[bytes, bytes]] = (),
    ):
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": headers,
                "trailers": False,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
                "more_body": False,
            }
        )

    async def send_plain_text(self, send: "ASGISendCallable", content: str, *, status: int = 200):
        await self.send(
            send=send,
            body=content.encode("utf-8"),
            status=status,
            headers=[(b"Content-Type", b"text/plain; charset=utf-8")],
        )

    async def send_json(
        self,
        send: "ASGISendCallable",
        content: Any,
        *,
        status: int = 200,
        encoder: Optional[Type[json.JSONEncoder]] = None,
    ):
        body = json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            cls=encoder,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")
        await self.send(
            send=send,
            body=body,
            status=status,
            headers=[(b"Content-Type", b"application/json; charset=utf-8")],
        )
