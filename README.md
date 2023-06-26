# Deta Space Actions

Python package to interact with Deta Space Actions.

Ported from the Node package [deta-space-actions](https://www.npmjs.com/package/deta-space-actions).

This package is somewhat temporary, hopefully its functionality will be implemented in a future version of the official [Deta Python SDK](https://github.com/deta/deta-python).

## Features

- Dependency-free
- Includes type hints
- Supports Python 3.8 and above
- Object-oriented interface for defining and invoking actions
- Generic ASGI middleware
- Optional type checking support for the middleware

## TODO

- [ ] Finish writing it
  - [ ] Invocation function
- [ ] Write a README

## Installation

To install the latest in-development version:

```shell
python -m pip install git+https://github.com/lemonyte/deta-space-actions
```

Or, to install a specific commit:

```shell
python -m pip install git+https://github.com/lemonyte/deta-space-actions@{commit}
```

If you want full type checking support for the ASGI middleware, you'll also need to install [`asgiref`](https://github.com/django/asgiref) with:

```shell
python -m pip install asgiref
```

Or use the optional dependency syntax:

```shell
python -m pip install "deta-space-actions[typing] @ git+https://github.com/lemonyte/deta-space-actions"
```

## Usage

### Using the middleware

The package provides a generic ASGI middleware class that can be used with any ASGI framework.

```python
from deta_space_actions import Actions, ActionsMiddleware, Input, InputType


# Define an action handler.
async def hello(payload):
    return f"Hello, {payload['name']}!"


# Create an Actions instance.
actions = Actions()

# Add an action.
actions.add(
    name="hello",
    handler=hello,
    inputs=[
        Input(
            name="name",
            type=InputType.STRING,
            optional=False,
        ),
    ],
    title="Say hello",
)

# Create an ASGI app.
app = ...
# Add the middleware if your framework has a helper method for adding middleware.
app.add_middleware(ActionsMiddleware, actions=actions)
# Otherwise, wrap the app instance.
app = ActionsMiddleware(app, actions=actions)
```

### Using your own path handler

Alternatively, you can write your own handler function and use it with your framework's routing system.
An example for FastAPI is shown below.

```python
import json

from fastapi import FastAPI, HTTPException, Request

from deta_space_actions import Actions, Input, InputType


# Define an action handler.
async def hello(payload):
    return f"Hello, {payload.get('name', 'world')}!"


# Create an Actions instance.
actions = Actions()

# Add an action.
actions.add(
    name="hello",
    handler=hello,
    inputs=[
        Input(
            name="name",
            type=InputType.STRING,
            optional=False,
        ),
    ],
    title="Say hello",
)

# Create a FastAPI app.
app = FastAPI()


# Define a path handler.
@app.post("/__space/actions/{action_name}")
async def actions_handler(action_name: str, request: Request):
    action = actions.get(action_name)
    if not action:
        raise HTTPException(404)
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        payload = {}
    return await action.run(payload)
```

## License

[MIT License](LICENSE.txt)
