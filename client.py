import argparse
import sys
import socket
import json
import time
import logging
from threading import Thread

import logs.log_configs.client_log_config
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, DEFAULT_IP_ADDRESS,\
     DEFAULT_PORT, MESSAGE, TEXT, SENDER, RECIPIENT, EXIT
from common.utils import get_message, send_message
from common.decorators import log
from common.descriptors import Port
from common.metaclasses import ClientVerifier

logger = logging.getLogger('app.client')


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

    return server_address, server_port, client_name


class Client(metaclass=ClientVerifier):
    server_port = Port()
    
    def __init__(self, server_address, server_port, client_name):
        self.server_port = server_port
        self.server_address = server_address
        self.client_name = client_name

        self.transport = None
        self.receiver = None
        self.interface = None

        self.AVAILABLE_COMMANDS = 'available commands:\n' \
                                  'message - send message. enter the destination and the text in the next step\n' \
                                  'help - just help\n' \
                                  'exit - close program'

    @staticmethod
    def create_presence(account_name: str = 'Guest') -> dict:
        # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
        out = {ACTION: PRESENCE, TIME: time.time(), USER: {ACCOUNT_NAME: account_name}}
        return out

    def create_exit_message(self) -> dict:
        out = {ACTION: EXIT, TIME: time.time(), USER: {ACCOUNT_NAME: self.client_name}}
        return out

    def create_message(self) -> dict:
        recipient_name = input('Enter the recipient name (available names: "client_1", "client_2", "client_3"): ')
        message = input('Enter message: ')
        prepared_message = {
            ACTION: MESSAGE,
            TIME: time.time(),
            SENDER: self.client_name,
            RECIPIENT: recipient_name,
            TEXT: message}
        logger.info(f'Message prepared for sending {prepared_message}')
        return prepared_message

    @staticmethod
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

    def init_client(self):
        logger.info(f'Запущен клиент с параметрами:'
                    f'адрес сервера: {self.server_address}, порт: {self.server_port}, имя "{self.client_name}"')
        print(f'console messanger. client name: {self.client_name}')

        #  Инициализация сокета и обмен
        try:
            self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.transport.connect((self.server_address, self.server_port))

            message_to_server = self.create_presence(self.client_name)
            logger.info(f'Создано сообщение для сервера: {message_to_server}')
            send_message(self.transport, message_to_server)
            try:
                answer = self.process_ans(get_message(self.transport))
                logger.info(f'Получен ответ от сервера: {answer}')
            except (ValueError, json.JSONDecodeError):
                logger.error('He удалось декодировать сообщение сервера.')
                print('He удалось декодировать сообщение сервера.')
        except Exception as error:
            logger.critical(f'something went wrong: {error}')
            sys.exit(1)
        else:
            print('connected to server')

    def get_message_from_server(self):
        while True:
            try:
                message = get_message(self.transport)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        TIME in message and SENDER in message and RECIPIENT in message and \
                        message[RECIPIENT] == self.client_name and TEXT in message:

                    logger.info(f'получено сообщение от {message[SENDER]}: {message[TEXT]}')
                    print(f'\nПолучено сообщение от {message[SENDER]}: {message[TEXT]}.\nEnter command: ', end='')
                elif RESPONSE in message and ERROR in message:
                    logger.info(f'получено сообщение от сервера {message[ERROR]}')
                    print(f'\nПолучено сообщение от сервера {message[ERROR]}.\nEnter command: ', end='')
                else:
                    logger.info(f'получено некорректное сообщение {message}')
            except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                logger.critical(f'соединение с сервером {self.transport.getpeername()} потеряно')
                sys.exit(1)

    def interact_with_user(self):
        print(self.AVAILABLE_COMMANDS)

        while True:
            command = input('Enter command: ')

            if command == 'exit':
                try:
                    message = self.create_exit_message()
                    send_message(self.transport, message)
                    logger.info(f'client {self.client_name} entered "exit".')
                    logger.info(f'Exit message sent to server')
                    return
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    logger.critical(f'соединение с сервером {self.transport.getpeername()} потеряно')
                    sys.exit(1)
            elif command == 'help':
                logger.info(f'client {self.client_name} asked for help.')
                print(self.AVAILABLE_COMMANDS)
            elif command == 'message':
                try:
                    message = self.create_message()
                    send_message(self.transport, message)
                    logger.info(f'Message sent to client {message["recipient"]}')
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    logger.critical(f'соединение с сервером {self.transport.getpeername()} потеряно')
                    sys.exit(1)
            else:
                print('Please use command from the list above')

    def start_threads(self):
        # запуск потоков
        # receiver для получения ответов от сервера
        self.receiver = Thread(target=self.get_message_from_server)
        self.receiver.daemon = True
        self.receiver.start()

        # interface для взаимодействия с пользователем и отправки сообщений на сервер
        self.interface = Thread(target=self.interact_with_user)
        self.interface.daemon = True
        self.interface.start()

        logger.debug('threads started')

    def main_loop(self):
        # Основной цикл, если один из потоков завершён,
        # то значит, или потеряно соединение, или пользователь ввёл exit.
        while True:
            time.sleep(1)
            if self.receiver.is_alive() and self.interface.is_alive():
                continue
            break


def main():

    # server_address, server_port, client_name = get_client_parameters()

    client = Client(*get_client_parameters())
    client.init_client()
    client.start_threads()
    client.main_loop()


if __name__ == '__main__':
    main()
