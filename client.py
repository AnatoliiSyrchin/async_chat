import argparse
import sys
import socket
import json
import time
import logging
import threading
from threading import Thread, Lock

import logs.log_configs.client_log_config
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, DEFAULT_IP_ADDRESS,\
    DEFAULT_PORT, MESSAGE, TEXT, SENDER, RECIPIENT, EXIT, GET_CONTACTS, ALL_USERS, CONTACTS, ADD_CONTACT, \
    REMOVE_CONTACT, USERS_REQUEST, CONTACT_NAME
from common.utils import get_message, send_message
from common.decorators import log
from common.descriptors import Port
from common.metaclasses import ClientVerifier
from db.client_datebase import ClientStorage

logger = logging.getLogger('app.client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


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
    
    def __init__(self, server_address, server_port, client_name, datebase):
        self.server_port = server_port
        self.server_address = server_address
        self.client_name = client_name
        self.client_datebase = datebase

        self.transport = None
        self.receiver = None
        self.interface = None

        self.AVAILABLE_COMMANDS = 'available commands:\n' \
                                  'message - send message. enter the destination and the text in the next step\n'\
                                  'history - message history\n'\
                                  'contacts - contacts list\n'\
                                  'edit - edit contact list\n'\
                                  'help - just help\n' \
                                  'exit - close program'

    def fill_database(self):
        self.request_all_users()
        self.request_contacts()


    def request_all_users(self):
        prepared_message = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name,
        }
        send_message(self.transport, prepared_message)


    def request_contacts(self):
        prepared_message = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name,
        }
        send_message(self.transport, prepared_message)

    
    def add_contact(self, contact_name):
        prepared_message = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name,
            CONTACT_NAME: contact_name,
        }

        send_message(self.transport, prepared_message)
        time.sleep(1)
        
    def del_contact(self, contact_name):
        prepared_message = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name,
            CONTACT_NAME: contact_name,
        }

        send_message(self.transport, prepared_message)
        time.sleep(1)
        
    def print_history(self):
        request = input('Enter in, in - incoming messages, out - outcoming message, enter - all: ')
        if request =='in':
            for message in self.client_datebase.get_message_history(to_user=self.client_name):
                print(f'Incoming message from user {message.from_user}, message: {message.message}')
        elif request =='out':
            for message in self.client_datebase.get_message_history(from_user=self.client_name):
                print(f'Outcoming message to user: {message.to_user}, message: {message.message}')
        else:
            for message in self.client_datebase.get_message_history():
                print(f'From user {message.from_user}, to user: {message.to_user}, message: {message.message}')
    
    def print_contacts(self):
        print(f'{", ".join(self.client_datebase.get_contacts())}')

    def create_presence(self) -> dict:
        # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
        out = {ACTION: PRESENCE, TIME: time.time(), USER: {ACCOUNT_NAME: self.client_name}}
        return out

    def create_exit_message(self) -> dict:
        out = {ACTION: EXIT, TIME: time.time(), USER: {ACCOUNT_NAME: self.client_name}}
        return out

    def create_message(self) :
        contacts = self.client_datebase.get_contacts()
        if contacts:
            recipient_name = input(f'Enter the recipient name (available names: {", ".join(contacts)}): ')
            message = input('Enter message: ')
            with database_lock:
                if not self.client_datebase.check_user(recipient_name):
                    logger.error('No such user')
                    raise ValueError('No such user')
        else:
            print('You dont have any contacts, you should use edit, and add some')
            return
                        
        prepared_message = {
            ACTION: MESSAGE,
            TIME: time.time(),
            SENDER: self.client_name,
            RECIPIENT: recipient_name,
            TEXT: message}
        logger.info(f'Message prepared for sending {prepared_message}')

        with database_lock:
            self.client_datebase.save_message(self.client_name, recipient_name, message)

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

            message_to_server = self.create_presence()
            logger.info(f'Создано сообщение для сервера: {message_to_server}')
            send_message(self.transport, message_to_server)

            answer = self.process_ans(get_message(self.transport))
            logger.info(f'Получен ответ от сервера: {answer}')
        except (ValueError, json.JSONDecodeError):
            logger.error('He удалось декодировать сообщение сервера.')
            print('He удалось декодировать сообщение сервера.')
            sys.exit(1)
        except Exception as error:
            logger.critical(f'something went wrong: {error}')
            sys.exit(1)
        else:
            print('connected to server')

    def get_message_from_server(self):
        logger.info('get message from server')
        while True:
            try:
                message = get_message(self.transport)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        TIME in message and SENDER in message and RECIPIENT in message and \
                        message[RECIPIENT] == self.client_name and TEXT in message:
                    logger.info(f'получено сообщение от {message[SENDER]}: {message[TEXT]}')
                    with database_lock:
                        self.client_datebase.add_contact(message[SENDER])
                        self.client_datebase.save_message(message[SENDER], message[RECIPIENT], message[TEXT])
                    print(f'\nПолучено сообщение от {message[SENDER]}: {message[TEXT]}.\nEnter command: ', end='')

                elif RESPONSE in message and ERROR in message:
                    logger.info(f'ERROR получено сообщение от сервера {message[ERROR]}')
                    print(f'\nПолучено сообщение от сервера {message[ERROR]}.\nEnter command: ', end='')
                
                elif RESPONSE in message and CONTACTS in message:
                    with database_lock:
                        for contact in message[CONTACTS]:
                            self.client_datebase.add_contact(contact)

                if RESPONSE in message and ALL_USERS in message:
                    self.all_users = message[ALL_USERS]
                    with database_lock:
                        self.client_datebase.fill_all_users(self.all_users)
                
                elif RESPONSE in message and message[RESPONSE] == 200 and ADD_CONTACT in message:
                    with database_lock:
                        self.client_datebase.add_contact(message[ADD_CONTACT])
                        print(f'user {message[ADD_CONTACT]} added to contacts')
                
                elif RESPONSE in message and message[RESPONSE] == 200 and REMOVE_CONTACT in message:
                    with database_lock:
                        self.client_datebase.del_contact(message[REMOVE_CONTACT])
                        print(f'user {message[REMOVE_CONTACT]} removed from contacts')

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
                with sock_lock:
                    try:
                        message = self.create_message()
                        if message:
                            send_message(self.transport, message)
                            logger.info(f'Message sent to client {message["recipient"]}')
                    except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                        logger.critical(f'соединение с сервером {self.transport.getpeername()} потеряно')
                        sys.exit(1)
                    except ValueError as err:
                        print(err)
            
            elif command == 'edit':
                self.request_all_users()
                contacts = self.client_datebase.get_contacts()
                if contacts:
                    print(f'Your contacts: {", ".join(contacts)}')
                action = input('add - add contacts, del - delete contact: ')
                if action == 'add':
                    all_users = self.client_datebase.get_all_users()
                    print(f'avaible contacts: {", ".join(all_users)}')
                    new_contact = input('choose contact to add: ')
                    self.add_contact(new_contact)

                elif action == 'del':
                    contact_to_delete = input(f'choose contact to delite: ')
                    self.del_contact(contact_to_delete)
            
            elif command == 'history':
                self.print_history()

            elif command == 'contacts':
                self.print_contacts()

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
    server_address, server_port, client_name = get_client_parameters()
    client_datebase = ClientStorage(f'{client_name}_')
    client = Client(server_address, server_port, client_name, client_datebase)
    client.init_client()
    client.request_contacts()
    client.start_threads()

    client.main_loop()

if __name__ == '__main__':
    main()
