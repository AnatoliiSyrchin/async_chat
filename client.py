import argparse
import sys
import socket
import json
import time
import logging
from threading import Thread

import logs.log_configs.client_log_config
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, DEFAULT_IP_ADDRESS,\
     DEFAULT_PORT, MESSAGE,TEXT, SENDER, RECIPIENT, EXIT
from common.utils import get_message, send_message
from common.decorators import log

logger = logging.getLogger('app.client')
AVAILABLE_COMMANDS = 'available commands:\n'\
    'message - send message. enter the destination and the text in the next step\n'\
    'help - just help\n'\
    'exit - close program'


@log
def create_presence (account_name: str = 'Guest') -> dict:
    # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
    out = {ACTION: PRESENCE, TIME: time.time(), USER: {ACCOUNT_NAME: account_name}}
    return out


@log
def create_exit_message(account_name: str = 'Guest') -> dict:
    out = {ACTION: EXIT, TIME: time.time(), USER: {ACCOUNT_NAME: account_name}}
    return out


@log
def interact_with_user(sock, client_name):
    print(AVAILABLE_COMMANDS)
    
    while True:
        command = input('Enter command: ')
        
        if command == 'exit':
            try:
                message = create_exit_message(client_name)
                send_message(sock, message)
                logger.info(f'client {client_name} entered "exit".')
                logger.info(f'Exit message sent to server')
                return
            except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                logger.critical(f'соединение с сервером {sock.getpeername()} потеряно')
                sys.exit(1)
        elif command == 'help':
                logger.info(f'client {client_name} asked for help.')
                print(AVAILABLE_COMMANDS)
        elif command == 'message':
            try:
                message = create_message(client_name)
                send_message(sock, message)
                logger.info(f'Message sent to client {message["recipient"]}')
            except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                logger.critical(f'соединение с сервером {sock.getpeername()} потеряно')
                sys.exit(1)
        else:
            print('Please use command from the list above')


@log
def create_message(account_name: str = 'Guest'):
    recipient_name = input('Enter the recipient name (available names: "client_1", "client_2", "client_3"): ')
    message = input('Enter message: ')
    prepared_message = {
        ACTION: MESSAGE,
        TIME: time.time(),
        SENDER: account_name,
        RECIPIENT: recipient_name,
        TEXT: message}
    logger.info(f'Message prepared for sending {prepared_message}')
    return prepared_message


@log
def get_message_from_server(sock: socket.socket, client_name: str):
    while True:
        try:
            message = get_message(sock)
            if ACTION in message and message[ACTION] == MESSAGE and \
                    TIME in message and SENDER in message and RECIPIENT in message and \
                    message[RECIPIENT] == client_name and TEXT in message:

                logger.info(f'получено сообщение от {message[SENDER]}: {message[TEXT]}')
                print(f'\nПолучено сообщение от {message[SENDER]}: {message[TEXT]}.\nEnter command: ', end='')
            elif RESPONSE in message and ERROR in message:
                logger.info(f'получено сообщение от сервера {message[ERROR]}')
                print(f'\nПолучено сообщение от сервера {message[ERROR]}.\nEnter command: ', end='')
            else:
                logger.info(f'получено некорректное сообщение {message}')
        except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
            logger.critical(f'соединение с сервером {sock.getpeername()} потеряно')
            sys.exit(1)


@log
def process_ans(message: dict) -> str:
    """
    Функция разбирает ответ сервера
    :param message:
    :return:
    """
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {message[ERROR]}'
    raise ValueError


@log
def get_client_parameters() -> tuple:
    """Загружаем параметры командной строки"""
    # client.py 192.168.57.33 8079
    # server.py -p 8079 -a 192.168.57.33
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    if client_name is None:
        logger.critical(f'не указано имя клиента\nПосле параметра -\'n\' необходимо указать имя клиента.')
        sys.exit(1)
    if server_port < 1024 or server_port > 65535:
        logger.critical('В качестве порта может быть указано только число в диапазоне от 1024 до 65535')
        sys.exit(1)

    return server_address, server_port, client_name


def main():

    server_address, server_port, client_name = get_client_parameters()
    logger.info(f'Запущен клиент с параметрами:'
                f'адрес сервера: {server_address}, порт: {server_port}, имя "{client_name}"')
    print(f'console messanger. client name: {client_name}')

    #  Инициализация сокета и обмен
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))

        message_to_server = create_presence(client_name)
        logger.info(f'Создано сообщение для сервера: {message_to_server}')
        send_message(transport, message_to_server)
        try:
            answer = process_ans(get_message(transport))
            logger.info(f'Получен ответ от сервера: {answer}')
        except (ValueError, json.JSONDecodeError):
            logger.error('He удалось декодировать сообщение сервера.')
            print('He удалось декодировать сообщение сервера.')
    except Exception as error:
        logger.critical(f'something went wrong: {error}')
        sys.exit(1)
    else:
        print('connected to server')

        # запуск потоков
        # receiver для получения ответов от сервера
        receiver = Thread(target=get_message_from_server, args=(transport, client_name))
        receiver.daemon = True
        receiver.start()

        # interface для взаимодействия с пользователем и отправки сообщений на сервер
        interface = Thread(target=interact_with_user, args=(transport, client_name))
        interface.daemon = True
        interface.start()

        logger.debug('threads started')

        # Основной цикл, если один из потоков завершён,
        # то значит, или потеряно соединение, или пользователь ввёл exit.
        while True:
            time.sleep(1)
            if receiver.is_alive() and interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
