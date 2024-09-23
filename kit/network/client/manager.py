from kit import Manager

from .client import BaseClient
from .dispatcher import ClientDispatcher


class ClientNetworkManager(Manager, init=False):
    client: BaseClient
    dispatcher: ClientDispatcher

    def __init__(
        self, 
        client: BaseClient,
        dispatcher: ClientDispatcher
    ) -> None:
        super().__init__()

        self.client = client
        self.dispatcher = dispatcher
