from typing import Any, ClassVar
from pydantic import BaseModel, ConfigDict


class Update(BaseModel):
    update_type: ClassVar[int] = -1


class Callback(Update):
    result: Any
    callback_id: int


class UpdatesFactory:
    data: list[type[Update]]

    def __init__(self, data: list[type[Update]]) -> None:
        self.data = [
            Callback
        ] + data

        for i, update in enumerate(self.data):
            update.update_type = i

    def from_dict(self, update_dict: dict) -> Update:        
        factory = self.data[update_dict["type"]]
        
        return factory.model_validate(update_dict["data"])
