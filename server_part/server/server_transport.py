"""main server module"""
import binascii
import hmac
import os
import sys
import socket
import json
import logging
import select
from threading import Lock

from server_part.common.variables import MAX_CONNECTIONS, ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, MESSAGE, TEXT, SENDER, RECIPIENT, EXIT, GET_CONTACTS, ALL_USERS, CONTACTS, ADD_CONTACT, \
    REMOVE_CONTACT, USERS_REQUEST, CONTACT_NAME, PUBLIC_KEY, PASSWORD_HASH, REGISTER, CONTACT_IS_ONLINE, CHECK_NAME
from server_part.common.utils import get_message, send_message
from server_part.common.descriptors import Port
from server_part.common.metaclasses import ServerVerifier

from PyQt5.QtGui import QStandardItemModel, QStandardItem

# sys.path.append(os.getcwd())

logger = logging.getLogger('app.server')
socket_lock = Lock()


class ServerTransport(metaclass=ServerVerifier):
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
        print('Server')
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

        # registration
        if ACTION in message and message[ACTION] == REGISTER and TIME in message \
                and ACCOUNT_NAME in message and PASSWORD_HASH in message:

            result = self.server_base.add_user(message[ACCOUNT_NAME], message[PASSWORD_HASH])
            logger.debug(result)
            if result:
                logger.info('RESPONSE: 200, account registered')
                send_message(sock, {RESPONSE: 200})
                # self.all_clients.remove(sock)
                # sock.close()
            else:
                logger.info('RESPONSE: 400, ERROR: "account name already exists"')
                send_message(sock, {RESPONSE: 409})
            self.all_clients.remove(sock)
            sock.close()
            return

        # check user is registered
        if ACTION in message and message[ACTION] == CHECK_NAME and TIME in message \
                and ACCOUNT_NAME in message:

            result = self.server_base.check_user(message[ACCOUNT_NAME])
            if result:
                logger.info('RESPONSE: 200, account registered')
                send_message(sock, {RESPONSE: 200})
                # self.all_clients.remove(sock)
                # sock.close()
            else:
                logger.info('RESPONSE: 401, ERROR: account not registered')
                send_message(sock, {RESPONSE: 401, ERROR: 'account not registered'})
            self.all_clients.remove(sock)
            sock.close()
            return

        # presence
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
                and ACCOUNT_NAME in message and PUBLIC_KEY in message:
            self.authorize_user(message, sock)
            return

        elif ACTION in message and message[ACTION] == EXIT and TIME in message and \
                ACCOUNT_NAME in message:
            del self.names[message[ACCOUNT_NAME]]
            self.all_clients.remove(sock)
            self.server_base.user_logout(message[ACCOUNT_NAME])
            sock.close()
            return

        elif ACTION in message and message[ACTION] == MESSAGE and TIME in message and \
                SENDER in message and RECIPIENT in message and TEXT in message:
            self.requests.append((sock, message))
            logger.info(f'recived message {message[RECIPIENT]}, {message}')
            self.server_base.process_message(message[SENDER], message[RECIPIENT])
            send_message(sock, {RESPONSE: 200})
            return

        elif ACTION in message and message[ACTION] == GET_CONTACTS and USER in message and \
                self.names[message[USER]] == sock:
            contacts = self.server_base.get_contacts(message[USER])
            send_message(sock, {RESPONSE: 202, CONTACTS: contacts})

        elif ACTION in message and message[ACTION] == ADD_CONTACT and CONTACT_NAME in message and \
                ACCOUNT_NAME in message and self.names[message[ACCOUNT_NAME]] == sock:
            self.server_base.add_contact(message[ACCOUNT_NAME], message[CONTACT_NAME])
            send_message(sock, {RESPONSE: 200, ADD_CONTACT: message[CONTACT_NAME]})

        elif ACTION in message and message[ACTION] == CONTACT_IS_ONLINE and CONTACT_NAME in message:
            result = self.server_base.check_contact_is_online(message[CONTACT_NAME])
            send_message(sock, {RESPONSE: 200, CONTACT_IS_ONLINE: result})

        elif ACTION in message and message[ACTION] == PUBLIC_KEY and CONTACT_NAME in message:
            result = self.server_base.get_public_key(message[CONTACT_NAME])
            send_message(sock, {RESPONSE: 200, PUBLIC_KEY: result})

        elif ACTION in message and message[ACTION] == REMOVE_CONTACT and CONTACT_NAME in message and \
                ACCOUNT_NAME in message and self.names[message[ACCOUNT_NAME]] == sock:
            self.server_base.remove_contact(message[ACCOUNT_NAME], message[CONTACT_NAME])
            send_message(sock, {RESPONSE: 200, REMOVE_CONTACT: message[CONTACT_NAME]})

        elif ACTION in message and message[ACTION] == USERS_REQUEST and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == sock:
            all_users = [user.username for user in self.server_base.get_all_users()]
            send_message(sock, {RESPONSE: 202, ALL_USERS: all_users})

        else:
            send_message(sock, {RESPONSE: 400, ERROR: 'Bad Request'})
            return

    def authorize_user(self, message, client_socket):
        logger.debug(f'authorize_user  {message}')
        client_name = message[ACCOUNT_NAME]
        public_key = message[PUBLIC_KEY]
        if client_name not in self.names.keys():
            check_result = self.server_base.check_user(client_name)
            logger.debug(f'checked user in base {check_result}')
            if not check_result:
                logger.info('RESPONSE: 400, ERROR: "account name not registered"')
                send_message(client_socket, {RESPONSE: 400, ERROR: "account name not registered"})
                self.all_clients.remove(client_socket)
                client_socket.close()
            # checking password
            random_str = binascii.hexlify(os.urandom(64))
            random_str_decoded = random_str.decode('ascii')
            pass_hash = self.server_base.get_pass_hash(client_name).encode('utf-8')
            hashed_message = hmac.new(pass_hash, random_str, 'sha256')
            digest = hashed_message.digest()

            message_auth = {RESPONSE: 511, TEXT: random_str_decoded}
            logger.debug(f'Auth message = {message_auth}')
            send_message(client_socket, message_auth)
            answer = get_message(client_socket)

            client_answer = binascii.a2b_base64(answer[TEXT].encode('ascii'))

            logger.debug(f'received client_hashed_message {client_answer} {digest}')
            if RESPONSE in answer and answer[RESPONSE] == 511 and hmac.compare_digest(digest, client_answer):
                self.names[client_name] = client_socket
                send_message(client_socket, {RESPONSE: 200})
                self.server_base.user_login(client_name, *client_socket.getpeername(), public_key)

            else:
                try:
                    send_message(client_socket, {RESPONSE: 400, ERROR: 'Неверный пароль.'})
                except OSError:
                    pass
                self.all_clients.remove(client_socket)
                client_socket.close()

        else:
            logger.info('RESPONSE: 400, ERROR: "account name already exists"')
            send_message(client_socket, {RESPONSE: 400, ERROR: 'account name already exists'})
            self.all_clients.remove(client_socket)
            client_socket.close()

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
                logger.info('recipient in self.names')
                recipient_socket = self.names[recipient]
                logger.info(f'recipient socket {self.names[recipient]}')
                try:
                    with socket_lock:
                        logger.info(f'trying to send message {recipient} {message}')
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

    def create_history_model(self):
        hist_list = self.server_base.users_events_history()

        list_model = QStandardItemModel()
        list_model.setHorizontalHeaderLabels(
            ['Client name', 'Last visit', 'Messages sent', 'Messages received'])
        for user in hist_list:
            username = user.user.username
            login_time = user.user.last_login.strftime("%d.%m.%Y %H:%M")
            sent = str(user.sent)
            received = str(user.received)

            user = QStandardItem(username)
            user.setEditable(False)
            last_seen = QStandardItem(login_time)
            last_seen.setEditable(False)
            sent = QStandardItem(str(sent))
            sent.setEditable(False)
            recvd = QStandardItem(str(received))
            recvd.setEditable(False)
            list_model.appendRow([user, last_seen, sent, recvd])
        return list_model


    def create_users_model(self):
        active_users = self.server_base.show_active_users()
        list_model = QStandardItemModel()
        list_model.setHorizontalHeaderLabels(['Client name', 'IP Adress', 'Port', 'Connection time'])
        for user in active_users:
            username = user.user.username
            ip_address = user.ip_address
            port = str(user.port)
            login_time = user.login_time.strftime("%d.%m.%Y %H:%M")

            user = QStandardItem(username)
            user.setEditable(False)
            ip = QStandardItem(ip_address)
            ip.setEditable(False)
            port = QStandardItem(str(port))
            port.setEditable(False)
            time = QStandardItem(login_time)
            time.setEditable(False)

            list_model.appendRow([user, ip, port, time])
        return list_model

