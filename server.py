import sys
import socket
import json
import logging
import select
import argparse
from threading import Thread

import logs.log_configs.server_log_config
from common.variables import DEFAULT_PORT, MAX_CONNECTIONS, ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME,\
    RESPONSE, ERROR, MESSAGE, TEXT, SENDER, RECIPIENT, EXIT, GET_CONTACTS, DATA, ADD_CONTACT, REMOVE_CONTACT, \
    USERS_REQUEST
from common.utils import get_message, send_message
from common.decorators import log
from common.descriptors import Port
from common.metaclasses import ServerVerifier
from common.server_datebase import ServerStorage


AVAILABLE_COMMANDS = 'available commands:\n'\
    'users - list of all users\n'\
    'connected - list of active users\n'\
    'loghist - login history\n'\
    'help - just help\n'\
    'exit - close program'

logger = logging.getLogger('app.server')


@log
def get_server_parameters():
    """
    Загрузка параметров командной строки,
    если нет параметров, то задаём значения по умолчанию.
    :return:
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', '--address', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])

    return namespace.address, namespace.port


class Server(metaclass=ServerVerifier):
    port = Port()

    def __init__(self, listen_address, listen_port, server_base):
        self.address = listen_address
        self.port = listen_port
        self.server_base = server_base

        self.all_clients = []
        self.requests = []
        self.names = {}
        self.transport = None

    def init_server(self):
        logger.info(f'Запущен сервер, порт для подключений: {self.port}, адрес: {self.address}')
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.transport.bind((self.address, self.port))
        except Exception as error:
            logger.error(f'exception in init_server {error}')
            sys.exit(1)

        # Слушаем порт
        self.transport.listen(MAX_CONNECTIONS)
        self.transport.settimeout(1)

    def process_client_message(self, sock: socket.socket, message: dict):
        """
        Обработчик сообщений от клиентов, принимает словарь-сообщение от клиента,
        проверяет корректность, возвращает словарь-ответ для клиента.
        :param message:
        :param sock:
        :return:
        """
        # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}

        if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
                and USER in message and ACCOUNT_NAME in message[USER]:

            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = sock
                self.server_base.user_login(message[USER][ACCOUNT_NAME], *sock.getpeername())
                send_message(sock, {RESPONSE: 200})
            else:
                logger.info('RESPONSE: 400, ERROR: "account name already exists"')
                send_message(sock, {RESPONSE: 400, ERROR: 'account name already exists'})
                self.all_clients.remove(sock)
                sock.close()
            return

        elif ACTION in message and message[ACTION] == EXIT and TIME in message and \
                USER in message and ACCOUNT_NAME in message[USER]:
            del self.names[message[USER][ACCOUNT_NAME]]
            self.all_clients.remove(sock)
            self.server_base.user_logout(message[USER][ACCOUNT_NAME])
            sock.close()
            return

        elif ACTION in message and message[ACTION] == MESSAGE and TIME in message and \
                SENDER in message and RECIPIENT in message and TEXT in message:
            self.requests.append((sock, message))
            self.server_base.process_message(message[SENDER], message[RECIPIENT])
            return
        
        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == sock:
            contacts = self.server_base.get_contacts(message[USER])
            send_message(sock, {RESPONSE: 202, DATA: contacts})

        elif ACTION in message and message[ACTION] == ADD_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == sock:
            self.server_base.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(sock, {RESPONSE: 200})

        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and ACCOUNT_NAME in message and USER in message \
                and self.names[message[USER]] == sock:
            self.server_base.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_message(sock, {RESPONSE: 200})

        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == sock:
            all_users = [user.username for user in self.server_base.get_all_users()]
            send_message(sock, {RESPONSE: 202, DATA: all_users})

        else:
            send_message(sock, {RESPONSE: 400, ERROR: 'Bad Request'})
            return

    def read_requests(self, r_clients: list):
        for read_waiting_client in r_clients:
            try:
                message_from_client = get_message(read_waiting_client)
                logger.info(f'Получили сообщение от клиента {read_waiting_client.getpeername()} {message_from_client}')
                self.process_client_message(read_waiting_client, message_from_client)
            except (ValueError, json.JSONDecodeError):
                logger.error('Принято некорректное сообщение от клиента.')
            except ConnectionError:
                self.all_clients.remove(read_waiting_client)
                for name, sock in self.names.items():
                    if sock == read_waiting_client:
                        del self.names[name]
                        self.server_base.user_logout(name)
                        logger.info(f'Соединение с клиентом {name} потеряно')
                        break

    def write_responses(self):
        while self.requests:
            sock, message = self.requests.pop()
            recipient = message[RECIPIENT]
            if recipient in self.names:
                recipient_socket = self.names[recipient]
                try:
                    send_message(recipient_socket, message)
                except ConnectionError:
                    self.all_clients.remove(recipient_socket)
                    del self.names[recipient]
                    logger.info(f'Соединение с клиентом {recipient} потеряно')
            else:
                send_message(sock, {RESPONSE: 400, ERROR: f'account name {recipient} does not exist'})
                logger.info(f'Клиент с именем {recipient} не существует')


    def main_loop(self):
        while True:

            try:
                client, client_address = self.transport.accept()
                logger.info(f'Установлено соединение с клиентом {client_address}')
                self.all_clients.append(client)
            except OSError:
                pass

            read_clients = []
            write_clients = []
            wait = 5
            try:
                read_clients, write_clients, [] = select.select(self.all_clients, self.all_clients, [], wait)
            except:
                pass

            self.read_requests(read_clients)
            if self.requests:
                self.write_responses()


def print_help():
    print(AVAILABLE_COMMANDS)


def main():
    server_base = ServerStorage()
    # logger.error(f'trying to import')

    server = Server(*get_server_parameters(), server_base)
    server.init_server()
    server_thread = Thread(target=server.main_loop)
    server_thread.daemon = True
    server_thread.start()
    # server.main_loop()

    print_help()

    while True:
        command = input('Введите комманду: ')
        if command == 'help':
            print_help()
        elif command == 'exit':
            break
        elif command == 'users':
            for client in server_base.show_all_users():
                print(f'User {client.username}, last_login {client.last_login.strftime("%d.%m.%Y %H:%M")}')
        elif command == 'connected':
            for client in server_base.show_active_users():
                print(f'User {client.user.username} connected at {client.login_time.strftime("%d.%m.%Y %H:%M")} '
                      f'from {client.ip_address}:{client.port}')

        elif command == 'loghist':
            name = input('Enter the username to view users history or press Enter for all history: ')
            for client in server_base.login_history(name):
                print(f'User {client.user.username} connected at {client.login_time.strftime("%d.%m.%Y %H:%M")} '
                      f'from {client.ip_address}:{client.port}')
        else:
            print('Команда не распознана.')



if __name__ == '__main__':
    main()
