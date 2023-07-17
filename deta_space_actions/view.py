from abc import ABCMeta, abstractmethod
from typing import Any, ClassVar, Optional, Sequence, Tuple, Union


class RawView:
    __slots__ = ("data",)
    id = "@deta/raw"

    def __init__(self, data: Any):
        self.data = data

    def as_serializable(self):
        return self.data


class DetailView:
    __slots__ = ("text", "title", "image_url", "url")
    id = "@deta/detail"

    def __init__(
        self,
        text: str,
        title: Optional[str] = None,
        image_url: Optional[str] = None,
        url: Optional[str] = None,
    ):
        self.text = text
        self.title = title
        self.image_url = image_url
        self.url = url

    def as_serializable(self):
        return {
            "title": self.title,
            "text": self.text,
            "image_url": self.image_url,
            "url": self.url,
        }


class FileView:
    __slots__ = ("url", "type", "name")
    id = "@deta/file"

    def __init__(self, url: str, type: str, name: Optional[str] = None):
        self.url = url
        self.type = type
        self.name = name

    def as_serializable(self):
        return {
            "url": self.url,
            "type": self.type,
            "name": self.name,
        }


class ListItem:
    __slots__ = ("title", "description", "url", "view")

    def __init__(
        self,
        title: str,
        description: Optional[str] = None,
        url: Optional[str] = None,
        view: Optional["View"] = None,
    ):
        self.title = title
        self.description = description
        self.url = url
        self.view = view

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "view": {
                "type": self.view.id,
                "data": self.view.as_serializable(),
            }
            if self.view
            else None,
        }


class ListView:
    __slots__ = ("items", "title", "description")
    id = "@deta/list"

    def __init__(self, items: Sequence[ListItem], title: Optional[str] = None, description: Optional[str] = None):
        self.items = items
        self.title = title
        self.description = description

    def as_serializable(self):
        return {
            "title": self.title,
            "description": self.description,
            "items": [item.to_dict() for item in self.items],
        }


class CustomView(BaseView):
    id = 'x'

    def __init__(self, data: Any, id: str):
        self.data = data
        self.id = id

    def as_serializable(self):
        return self.data


View = Union[RawView, DetailView, FileView, ListView, CustomView]
