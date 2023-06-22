import json
import os
import urllib.request

from .actions import HandlerInput


class App:
    def __init__(self, domain: str, api_key: str):
        self.base = domain if domain.startswith("http") else f"https://{domain}"
        api_key = api_key or os.environ.get("SPACE_API_KEY", "")
        if not api_key:
            raise ValueError("no API key provided")
        self.api_key = api_key

    def invoke(self, action: str, payload: HandlerInput):
        request = urllib.request.Request(f"{self.base}/__space/actions/{action}")
        request.add_header("Content-Type", "application/json")
        request.add_header("X-Space-API-Key", self.api_key)
        with urllib.request.urlopen(request, json.dumps(payload).encode("utf-8")) as response:
            # TODO: port this
            if response.getcode() != 200:
                raise ValueError(f"error invoking action: {response.statusText}")
            if response.headers.get("Content-Type") == "application/json":
                return response.json()
            return response.text()
