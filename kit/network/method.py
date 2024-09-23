from typing import Any, ClassVar
from pydantic import BaseModel


class Method(BaseModel):
    method_type: ClassVar[int] = -1
    return_type: ClassVar[Any] = None


class MethodsFactory:
    data: list[type[Method]]

    def __init__(self, data: list[type[Method]]) -> None:
        self.data = data

        for i, method in enumerate(self.data):
            method.method_type = i

    def from_dict(self, method_dict: dict) -> Method:
        factory = self.data[method_dict["type"]]
        
        return factory.model_validate(method_dict["data"])

