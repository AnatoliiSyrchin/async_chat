import json
from socket import socket
from common.variables import MAX_PACKAGE_LENGTH, ENCODING
from common.decorators import log
import logging
import logs.log_configs.server_log_config

logger = logging.getLogger('app.server')

@log
def get_message(sock) -> dict:
    '''
    Утилита приёма и декодирования сообщения
    принимает байты выдаёт словарь, если принято что-то другое отдаёт ошибку значения
    :param sock:
    :return:
    '''
    encoded_response = sock.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


@log
def send_message(sock, message: dict):
    '''
    Утилита кодирования и отправки сообщения принимает словарь и отправляет его
    :param sock:
    :param message:
    :return:
    '''
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)
