import json
from typing import Callable
from threading import Thread

from ..update import Update, UpdatesFactory
from .client import Client


class ClientDispatcher:
    client: Client
    updates_factory: UpdatesFactory
    
    def __init__(self, updates: UpdatesFactory) -> None:
        self.client = Client()
        self.updates_factory = updates
        self.updates_handlers = {
            0: self.client.resolve
        }

    def on(self, update: type[Update]) -> Callable:
        def _(function: Callable) -> None:
            self.updates_handlers[update.update_type] = function
        
        return _

    def process_update(self, update: Update) -> None:
        function = self.updates_handlers.get(update.update_type)

        if function is not None:
            function(update)

    def process_data(self, data: dict) -> None:
        update = self.updates_factory.from_dict(data)

        self.process_update(update)

    def process_receiver(self) -> None:
        all_data = b""

        while True:
            all_data += self.client.sock.recv(1024)
            
            while True:
                if all_data.count(b"\n") == 0:
                    break

                data, _, all_data = all_data.partition(b"\n")

                self.process_data(json.loads(data))

    def run(self) -> None:
        threads = [
            Thread(target=self.process_receiver),
            Thread(target=self.client.process_sender)
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    def run_in_thread(self) -> None:
        Thread(target=self.run).start()
