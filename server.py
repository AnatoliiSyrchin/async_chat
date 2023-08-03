import os
import sys
import socket
import json
import logging
import select
import argparse
import configparser
from threading import Thread, Lock

from PyQt5.QtGui import QStandardItemModel, QStandardItem

import logs.log_configs.server_log_config
from common.variables import DEFAULT_PORT, MAX_CONNECTIONS, ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME,\
    RESPONSE, ERROR, MESSAGE, TEXT, SENDER, RECIPIENT, EXIT, GET_CONTACTS, ALL_USERS, CONTACTS, ADD_CONTACT, \
    REMOVE_CONTACT, USERS_REQUEST, CONTACT_NAME
from common.utils import get_message, send_message
from common.decorators import log
from common.descriptors import Port
from common.metaclasses import ServerVerifier
from db.server_datebase import ServerStorage

from server_gui import MyMainWindow, ServerSettings, HistoryList, UsersList
from PyQt5.QtWidgets import QMessageBox, QApplication


AVAILABLE_COMMANDS = 'available commands:\n'\
    'users - list of all users\n'\
    'connected - list of active users\n'\
    'loghist - login history\n'\
    'help - just help\n'\
    'exit - close program'

logger = logging.getLogger('app.server')
socket_lock = Lock()


@log
def get_server_parameters(port=str(DEFAULT_PORT), address=''):
    """
    Загрузка параметров командной строки,
    если нет параметров, то задаём значения по умолчанию.
    :return:
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=int(port), type=int, nargs='?')
    parser.add_argument('-a', '--address', default=address, nargs='?')
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
                ACCOUNT_NAME in message:
            del self.names[message[ACCOUNT_NAME]]
            self.all_clients.remove(sock)
            self.server_base.user_logout(message[ACCOUNT_NAME])
            sock.close()
            return

        elif ACTION in message and message[ACTION] == MESSAGE and TIME in message and \
                SENDER in message and RECIPIENT in message and TEXT in message:
            self.requests.append((sock, message))
            logger.info(f'recived message {RECIPIENT}, {message}')
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


def server_config(config_tab, config, server):

    config_tab.select_base_path.setText(config['SETTINGS']['database_path'])
    config_tab.filename_field.setText(config['SETTINGS']['database_file'])
    config_tab.port_field.setText(config['SETTINGS']['default_port'])
    config_tab.ip_field.setText(config['SETTINGS']['listen_address'])
    config_tab.save_button.clicked.connect(lambda: save_server_config(config_tab, config, server))


def save_server_config(config_tab, config, server):

    message = QMessageBox()
    config['SETTINGS']['Database_path'] = config_tab.select_base_path.text()
    config['SETTINGS']['Database_file'] = config_tab.filename_field.text()
    try:
        port = int(config_tab.port_field.text())
    except ValueError:
        message.warning(config_tab, 'Error', 'Port must be an integer')
    else:
        config['SETTINGS']['Listen_Address'] = config_tab.ip_field.text()
        if 1023 < port < 65536:
            config['SETTINGS']['Default_port'] = str(port)
            with open('server.ini', 'w') as conf:
                config.write(conf)
                path = os.path.join(
                    config['SETTINGS']['Database_path'],
                    config['SETTINGS']['Database_file'])
                server.server_base = ServerStorage(path)
                message.setText('Settings successfully saved!')
                message.setIcon(QMessageBox.Information)
                message.exec_()
        else:
            message.warning(
                config_tab,
                'Error',
                'Port must be from 1024 to 65536')


def create_history_model(database):
    hist_list = database.users_events_history()

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


def create_users_model(database):
    active_users = database.show_active_users()
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


def refresh_tab(window, base, config, index, server=None):
    if index == 0:
        window.tab_1.table.setModel(create_users_model(server.server_base))
        window.tab_1.table.resizeColumnsToContents()
        window.tab_1.table.resizeRowsToContents()

    if index == 1:
        window.tab_2.table.setModel(create_history_model(server.server_base))
        window.tab_2.table.resizeColumnsToContents()
        window.tab_2.table.resizeRowsToContents()

    if index == 2:
        server_config(window.tab_3, config, server)


def main():

    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    listen_address, listen_port = get_server_parameters(config['SETTINGS']['Default_port'],
                                                        config['SETTINGS']['Listen_Address'])

    path_to_base_dir = config['SETTINGS']['Database_path'] or os.path.join(dir_path, 'db')
    path = os.path.join(path_to_base_dir, config['SETTINGS']['Database_file'])
    server_base = ServerStorage(path)

    # data for tests
    # server_base.user_login('alesha', '127.0.0.1', 7000)
    # server_base.user_login('masha', '127.0.0.2', 5000)
    # server_base.process_message('alesha', 'masha')

    server = Server(listen_address, listen_port, server_base)
    server.init_server()
    server_thread = Thread(target=server.main_loop)
    server_thread.daemon = True
    server_thread.start()

    server_app = QApplication(sys.argv)
    main_window = MyMainWindow()

    main_window.statusBar().showMessage('Server Working')

    # refresh widget on active tab
    refresh_tab(main_window, server_base, config, main_window.tab_widget.currentIndex(), server)

    main_window.show()

    # timer = QTimer()
    # timer.timeout.connect(list_update)
    # timer.start(1000)

    main_window.tab_1.refresh_button.clicked.connect(
        lambda: refresh_tab(main_window, server_base, config, main_window.tab_widget.currentIndex(), server))

    main_window.tab_2.refresh_button.clicked.connect(
        lambda: refresh_tab(main_window, server_base, config, main_window.tab_widget.currentIndex(), server))

    main_window.tab_widget.currentChanged.connect(
        lambda: refresh_tab(main_window, server_base, config, main_window.tab_widget.currentIndex(), server))

    # Start GUI
    server_app.exec_()


if __name__ == '__main__':
    main()
