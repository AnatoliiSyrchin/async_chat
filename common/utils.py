"""functions used both by clients and server"""
import json
from socket import socket
from common.variables import MAX_PACKAGE_LENGTH, ENCODING
from common.decorators import log
import logging
import logs.log_configs.server_log_config

logger = logging.getLogger('app.server')


# @log
def get_message(sock) -> dict:
    """
    The utility for receiving and decoding messages
    recives bytes, returns dict
    """
    encoded_response = sock.recv(MAX_PACKAGE_LENGTH)
    logger.debug(encoded_response)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


# @log
def send_message(sock: socket, message: dict):
    """
    The utility encoding messages to json
    end sending to the passed socket
    """
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)
