import sys
import socket
import json
import time
import logging

import logs.log_configs.client_log_config
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT, MESSAGE,TEXT, SENDER
from common.utils import get_message, send_message
from common.decorators import log

logger = logging.getLogger('app.client')

@log
def create_presence (account_name: str = 'Guest') -> dict:
    # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
    out = {ACTION: PRESENCE, TIME: time.time(), USER: {ACCOUNT_NAME: account_name } }
    return out

@log
def create_message(sock, account_name: str = 'Guest'):
    text = input('Enter message or "0" to exit: ')

    if text == '0':
        logger.info('client entered "0" and exited')
        sock.close()
        sys.exit(0)

    prepared_message = {ACTION: MESSAGE, TIME: time.time(), ACCOUNT_NAME: f'Client_{sock.fileno()}', TEXT: text }
    logger.info(f'Message prepared for sending {prepared_message}')
    return prepared_message

@log
def message_from_server(message: dict):
    if ACTION in message and message[ACTION] == MESSAGE and \
        TIME in message and SENDER in message and TEXT in message:
        logger.info(f'получено сообщение: {message[TEXT]} от {message[SENDER]}')
        print(f'получено сообщение: {message[TEXT]} от {message[SENDER]}')
    else:
        logger.info(f'получено некорректное сообщение {message}')

@log
def process_ans(message: dict) -> str:
    '''
    Функция разбирает ответ сервера
    :param message:
    :return:
    '''
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {message[ERROR]}'
    raise ValueError

@log
def get_client_parameters():
    # пока просто вынес в отдельную функцию, с парсером разберусь позже) наверно
    '''Загружаем параметы коммандной строки'''
    # cLient.py 192.168.57.33 8079
    # server.py -p 8079 -a 192.168.57.33
    try:
        if '-m' not in sys.argv:
            logger.critical('не указан тип клиента')
            sys.exit(1)
        mode = sys.argv[sys.argv.index('-m') + 1]
        if mode not in ('reader', 'writer'):
            logger.critical('тип клиента должеен быть "reader" или "writer"')
            sys.exit(1)
    except IndexError:
        logger.info('После параметра -\'m\' необходимо указать тип клиента.')
        sys.exit(1)

    try:
        server_address = sys.argv[1]
        if server_address == '-m':
            raise IndexError
        server_port = int(sys.argv[2])
        if server_port < 1024 or server_port > 65535:
            raise ValueError
        logger.info('Адрес и порт получены из командной строки')
    except IndexError:
        logger.info('Адрес и порт не указаны, используются значения по умолчанию')
        server_address = DEFAULT_IP_ADDRESS
        server_port = DEFAULT_PORT
    except ValueError:
        logger.critical('В качестве порта может быть указано только число в диапазоне от 1024 до 65535')
        # print('В качестве порта может быть указано только число в диапазоне от 1024 до 65535')
        sys.exit(1)
    return server_address, server_port, mode

    
def main():

    server_address, server_port, mode = get_client_parameters()
    logger.info(f'Запущен клиент с парамертами: адрес сервера: {server_address}, порт: {server_port}, тип {mode}')

    #  Инициализация сокета и обмен
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))

        message_to_server = create_presence()
        logger.info(f'Создано сообщение для сервера: {message_to_server}')
        send_message(transport, message_to_server)
        try:
            answer = process_ans(get_message(transport))
            logger.info(f'Получен ответ от сервера: {answer}')
        except (ValueError, json.JSONDecodeError):
            logger.error('He удалось декодировать сообщение сервера.')
            print('He удалось декодировать сообщение сервера.')
    except Exception as error:
        logger.critical(f'somethong went wrong: {error}')
    else:
        if mode == 'writer':
            print('send mode')
        else:
            print('receive mode')
        
        while True:
            if mode == 'writer':
                try:
                    send_message(transport, create_message(transport))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    logger.critical(f'соединение с сервером {server_address} потеряно')
                    sys.exit(1)
            if mode == 'reader':
                try:
                    message_from_server(get_message(transport))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    logger.critical(f'соединение с сервером {server_address} потеряно')
                    sys.exit(1)


if __name__ == '__main__':
    main()
