from bson.objectid import ObjectId

from pyfastocloud.fastocloud_client import FastoCloudClient, Fields
from pyfastocloud.client_handler import IClientHandler
from pyfastocloud.json_rpc import Request, Response
from pyfastocloud.client_constants import Commands, ClientStatus

from app.service.stream_handler import IStreamHandler
import app.common.constants as constants


class OperationSystem(object):
    __slots__ = ['name', 'version', 'arch']

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.__slots__:
                setattr(self, key, value)

    def __str__(self):
        return '{0} {1}({2})'.format(self.name, self.version, self.arch)


class ServiceClient(IClientHandler):
    HTTP_HOST = 'http_host'
    VODS_HOST = 'vods_host'
    CODS_HOST = 'cods_host'
    SUBSCRIBERS_HOST = 'subscribers_host'
    BANDWIDTH_HOST = 'bandwidth_host'
    VERSION = 'version'
    OS = 'os'

    @staticmethod
    def get_log_service_path(host: str, port: int, sid: str):
        return constants.DEFAULT_SERVICE_LOG_PATH_TEMPLATE_3SIS.format(host, port, sid)

    @staticmethod
    def get_log_stream_path(host: str, port: int, stream_id: str):
        return constants.DEFAULT_STREAM_LOG_PATH_TEMPLATE_3SIS.format(host, port, stream_id)

    @staticmethod
    def get_pipeline_stream_path(host: str, port: int, stream_id: str):
        return constants.DEFAULT_STREAM_PIPELINE_PATH_TEMPLATE_3SIS.format(host, port, stream_id)

    def __init__(self, sid: ObjectId, host: str, port: int, handler: IStreamHandler):
        self.id = sid
        self._request_id = 0
        self._handler = handler
        self._client = FastoCloudClient(host, port, self)
        self._set_runtime_fields()

    def connect(self):
        self._client.connect()

    def is_connected(self):
        return self._client.is_connected()

    def socket(self):
        return self._client.socket()

    def recv_data(self):
        data = self._client.read_command()
        self._client.process_commands(data)

    def status(self) -> ClientStatus:
        return self._client.status()

    def disconnect(self):
        self._client.disconnect()

    def activate(self, license_key: str):
        return self._client.activate(self._gen_request_id(), license_key)

    def ping_service(self):
        return self._client.ping_service(self._gen_request_id())

    def stop_service(self, delay: int):
        return self._client.stop_service(self._gen_request_id(), delay)

    def get_log_service(self, host: str, port: int):
        return self._client.get_log_service(self._gen_request_id(),
                                            ServiceClient.get_log_service_path(host, port, str(self.id)))

    def start_stream(self, config: dict):
        return self._client.start_stream(self._gen_request_id(), config)

    def stop_stream(self, stream_id: str):
        return self._client.stop_stream(self._gen_request_id(), stream_id)

    def restart_stream(self, stream_id: str):
        return self._client.restart_stream(self._gen_request_id(), stream_id)

    def get_log_stream(self, host: str, port: int, stream_id: str, feedback_directory: str):
        return self._client.get_log_stream(self._gen_request_id(), stream_id, feedback_directory,
                                           ServiceClient.get_log_stream_path(host, port, stream_id))

    def get_pipeline_stream(self, host: str, port: int, stream_id: str, feedback_directory: str):
        return self._client.get_pipeline_stream(self._gen_request_id(), stream_id, feedback_directory,
                                                ServiceClient.get_pipeline_stream_path(host, port, stream_id))

    def sync_service(self, settings):
        if not settings:
            return

        streams = []
        for stream in settings.streams:
            stream.set_server_settings(settings)
            streams.append(stream.config())

        subscribers = []
        for subs in settings.subscribers:
            conf = subs.to_service(settings)
            subscribers.append(conf)

        return self._client.sync_service(self._gen_request_id(), streams, subscribers)

    def prepare_service(self, settings):
        if not settings:
            return

        return self._client.prepare_service(self._gen_request_id(), settings.feedback_directory,
                                            settings.timeshifts_directory,
                                            settings.hls_directory,
                                            settings.playlists_directory,
                                            settings.dvb_directory,
                                            settings.capture_card_directory,
                                            settings.vods_in_directory,
                                            settings.vods_directory, settings.cods_directory)

    def get_http_host(self) -> str:
        return self._http_host

    def get_os(self) -> OperationSystem:
        return self._os

    def get_vods_host(self) -> str:
        return self._vods_host

    def get_cods_host(self) -> str:
        return self._cods_host

    def get_subscribers_host(self) -> str:
        return self._subscribers_host

    def get_bandwidth_host(self) -> str:
        return self._bandwidth_host

    def get_vods_in(self) -> list:
        return self._vods_in

    def get_version(self) -> str:
        return self._version

    # handler
    def process_response(self, req: Request, resp: Response):
        if not req:
            return

        if req.method == Commands.ACTIVATE_COMMAND and resp.is_message():
            if self._handler:
                result = resp.result
                subscribers_host = result.get(ServiceClient.SUBSCRIBERS_HOST, None)
                bandwidth_host = result.get(ServiceClient.BANDWIDTH_HOST, None)

                os = OperationSystem(**result[ServiceClient.OS])

                self._set_runtime_fields(result[ServiceClient.HTTP_HOST], result[ServiceClient.VODS_HOST],
                                         result[ServiceClient.CODS_HOST], subscribers_host, bandwidth_host,
                                         result[ServiceClient.VERSION], os)
                self._handler.on_service_statistic_received(result)

        if req.method == Commands.PREPARE_SERVICE_COMMAND and resp.is_message():
            for directory in resp.result:
                if Fields.VODS_IN_DIRECTORY in directory:
                    self._vods_in = directory[Fields.VODS_IN_DIRECTORY]['content']
                    break

    def process_request(self, req: Request):
        if not req:
            return

        if not self._handler:
            return

        if req.method == Commands.STATISTIC_STREAM_COMMAND:
            self._handler.on_stream_statistic_received(req.params)
        elif req.method == Commands.CHANGED_STREAM_COMMAND:
            self._handler.on_stream_sources_changed(req.params)
        elif req.method == Commands.STATISTIC_SERVICE_COMMAND:
            self._handler.on_service_statistic_received(req.params)
        elif req.method == Commands.QUIT_STATUS_STREAM_COMMAND:
            self._handler.on_quit_status_stream(req.params)
        elif req.method == Commands.CLIENT_PING_COMMAND:
            self._handler.on_ping_received(req.params)

    def on_client_state_changed(self, status: ClientStatus):
        if status != ClientStatus.ACTIVE:
            self._set_runtime_fields()
        if self._handler:
            self._handler.on_client_state_changed(status)

    # private
    def _set_runtime_fields(self, http_host=None, vods_host=None, cods_host=None, subscribers_host=None,
                            bandwidth_host=None,
                            version=None,
                            os=None,
                            vods_in=None):
        self._http_host = http_host
        self._vods_host = vods_host
        self._cods_host = cods_host
        self._subscribers_host = subscribers_host
        self._bandwidth_host = bandwidth_host
        self._version = version
        self._os = os
        self._vods_in = vods_in

    def _gen_request_id(self) -> int:
        current_value = self._request_id
        self._request_id += 1
        return current_value
