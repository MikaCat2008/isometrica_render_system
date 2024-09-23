import time, json, socket
from queue import Queue
from threading import Lock, Event

from ..method import Method
from .callback import Callback


class Client:
    lock: Lock
    sock: socket.socket
    sending_methods: list[tuple[Method, int]]

    callbacks: dict[int, Callback]
    callbacks_next_id: int


    def __init__(self) -> None:
        self.lock = Lock()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("localhost", 8080))
        self.sending_methods = []

        self.callbacks = {}
        self.callbacks_next_id = 0
 
    def resolve(self, callback: Callback) -> None:
        result = callback.result
        callback_id = callback.callback_id

        with self.lock:
            self.callbacks[callback_id].set_result(result)
            del self.callbacks[callback_id]
    
    def process_sender(self) -> None:
        while True:
            data = b"".join(
                json.dumps({
                    "id": callback_id,
                    "type": method.method_type,
                    "data": method.model_dump()
                }).encode() + b"\n"
                for method, callback_id in self.sending_methods
            )

            self.sock.sendall(data)
            self.sending_methods = []

            time.sleep(0.01)

    def __call__(self, method: Method) -> Callback:
        with self.lock:
            callback_id = self.callbacks_next_id
            self.callbacks_next_id += 1
                    
            callback = Callback(callback_id, method.return_type)
            self.callbacks[callback_id] = callback
        
            self.sending_methods.append((method, callback_id))

        return callback
