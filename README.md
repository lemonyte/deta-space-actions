# Deta Space Actions

Python package to interact with Deta Space Actions.

Ported from the Node package [deta-space-actions](https://www.npmjs.com/package/deta-space-actions).

This package is somewhat temporary, hopefully its functionality will be implemented in a future version of the official [Deta Python SDK](https://github.com/deta/deta-python).

## TODO

- [ ] Finish writing it
  - [ ] Generic ASGI middleware
  - [ ] Invocation function
- [ ] Write a README

## Installation

To install the latest in-development version:

```shell
pip install git+https://github.com/lemonyte/deta-space-actions
```

Or, to install a specific commit:

```shell
pip install git+https://github.com/lemonyte/deta-space-actions@{commit}
```

## Usage

```python
from deta_space_actions import Actions, Input, InputType


async def hello(payload):
    return f"Hello, {payload['name']}"


actions = Actions()

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
```

## License

[MIT License](LICENSE.txt)
