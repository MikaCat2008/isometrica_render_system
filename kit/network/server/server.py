import time, json, socket
from typing import Any
from threading import Lock

from ..update import Update


class Server:
    sock: socket.socket
    locks: dict[int, Lock]

    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("localhost", 8080))
        self.sock.listen()
        self.locks = {}

    def __call__(self, connection: socket.socket, update: Update) -> Any:
        data = update.model_dump()
        lock = self.locks.get(id(connection))

        with lock:
            try:
                connection.sendall(
                    json.dumps({
                        "type": update.update_type,
                        "data": data
                    }).encode() + b"\n"
                )
            except ConnectionError:
                ...

            time.sleep(0.01)
