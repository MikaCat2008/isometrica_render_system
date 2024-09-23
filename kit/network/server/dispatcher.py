import json, socket
from typing import Any, Callable, Optional
from threading import Lock, Thread

from ..update import Callback
from ..method import Method, MethodsFactory
from .server import Server


class ServerDispatcher:
    server: Server
    connections: list[socket.socket]
    methods_factory: MethodsFactory
    methods_handlers: dict[int, Callable]

    def __init__(self, methods: MethodsFactory) -> None:   
        self.server = Server()
        self.connections = []
        self.methods_factory = methods
        self.methods_handlers = {}

    def on(self, method_type: type[Method]) -> Callable:
        def _(function: Callable) -> None:
            self.methods_handlers[method_type.method_type] = function
        
        return _

    def process_data(self, data: dict) -> Optional[Callback]:
        method = self.methods_factory.from_dict(data)
        result = self.process_method(method)

        if result is not None:
            return Callback(
                result=result,
                callback_id=data["id"]
            )

    def process_method(self, method: Method) -> Any:
        function = self.methods_handlers.get(method.method_type)

        if function is not None:
            return function(method)

    def process_connection(self, connection: socket.socket) -> None:
        all_data = b""

        while True:
            try:
                all_data += connection.recv(1024)
            except ConnectionError:
                self.connections.remove(connection)

                return

            while True:
                if all_data.count(b"\n") == 0:
                    break

                data, _, all_data = all_data.partition(b"\n")
                callback = self.process_data(json.loads(data))

                if callback is not None:
                    self.server(connection, callback)

    def run(self) -> None:
        while True:
            connection = self.server.sock.accept()[0]

            self.server.locks[id(connection)] = Lock()
            self.connections.append(connection)
            Thread(target=self.process_connection, args=(connection, )).start()
