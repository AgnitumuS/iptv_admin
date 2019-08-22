from app.common.service.entry import ServiceSettings
from app.service.service import Service


class ServiceManager(object):
    def __init__(self, host: str, port: int, socketio):
        self._host = host
        self._port = port
        self._socketio = socketio
        self._stop_listen = False
        self._servers_pool = []

    def stop(self):
        self._stop_listen = True

    def find_or_create_server(self, settings: ServiceSettings) -> Service:
        for server in self._servers_pool:
            if server.id == settings.id:
                return server

        server = Service(self._host, self._port, self._socketio, settings)
        self.__add_server(server)
        return server

    def refresh(self):
        from gevent import select
        while not self._stop_listen:
            sockets = []
            for server in self._servers_pool:
                if server.is_connected():
                    sockets.append(server.socket())

            readable, _, _ = select.select(sockets, [], [], 1)
            for read in readable:
                for server in self._servers_pool:
                    if server.socket() == read:
                        server.recv_data()
                        break

    # private
    def __add_server(self, server: Service):
        self._servers_pool.append(server)
