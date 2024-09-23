from typing import Any, Generic, TypeVar, Callable
from threading import Event

from pydantic import TypeAdapter

T = TypeVar("T")


class Callback(Event, Generic[T]):
    result: Any
    adapter: TypeAdapter
    listeners: list[Callable]
    callback_id: int
    
    def __init__(self, callback_id: int, result_type: type) -> None:
        super().__init__()
        
        self.result = None
        self.adapter = TypeAdapter(result_type)
        self.listeners = []
        self.callback_id = callback_id
    
    def set_result(self, result: Any) -> None:
        self.result = self.adapter.validate_python(result)
        self.set()

        for listener in self.listeners:
            listener(self.result)
    
    def wait_result(self) -> T:
        if self.result_type is None:
            return None

        self.wait()
        
        return self.result

    def add_result_listener(self, listener: Callable) -> None:
        self.listeners.append(listener)
