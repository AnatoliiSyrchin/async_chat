import binascii
import hashlib
import hmac
import sys
import time
import logging
import json
import threading
import os
import base64
from socket import socket, AF_INET, SOCK_STREAM
from PyQt5.QtCore import pyqtSignal, QObject


sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)))
from common.utils import *
from common.variables import *
from common.errors import ServerError
from Crypto.Cipher import PKCS1_OAEP
import logs.log_configs.client_log_config

# Логер и объект блокировки для работы с сокетом.
logger = logging.getLogger('app.client')
socket_lock = threading.Lock()


# Класс - Транспорт, отвечает за взаимодействие с сервером
class ClientTransport(threading.Thread, QObject):
    # Сигналы новое сообщение и потеря соединения
    new_message = pyqtSignal(dict)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username, client_password, rsa_key):
        # Вызываем конструктор предка
        threading.Thread.__init__(self)
        QObject.__init__(self)

        # Класс База данных - работа с базой
        self.database = database
        # username, password, and public_key
        self.username = username
        self.password = client_password
        self.public_key = rsa_key.publickey().export_key().decode('ascii')

        # set server socket and connect
        self.transport = None
        self.connection_init(port, ip_address)
        # get users and contacts lists
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                logger.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            logger.error('Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            logger.critical(f'Потеряно соединение с сервером.')
            raise ServerError('Потеряно соединение с сервером!')
            # Флаг продолжения работы транспорта.
        self.running = True

    # Функция инициализации соединения с сервером
    def connection_init(self, port, ip):
        # Инициализация сокета и сообщение серверу о нашем появлении
        self.transport = socket(AF_INET, SOCK_STREAM)

        # Таймаут необходим для освобождения сокета.
        self.transport.settimeout(5)

        # Соединяемся, 5 попыток соединения, флаг успеха ставим в True если удалось
        connected = False
        for i in range(5):
            logger.info(f'Попытка подключения №{i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        # Если соединится не удалось - исключение
        if not connected:
            logger.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')

        logger.debug('Connected to server. trying to auth')

        passwd_bytes = self.password.encode('utf-8')
        salt = self.username.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)
        password_hash_decoded = passwd_hash_string.decode('ascii')

        # Посылаем серверу приветственное сообщение и получаем ответ что всё нормально или ловим исключение.
        try:
            with socket_lock:
                send_message(self.transport, self.create_presence())
                server_ans = get_message(self.transport)
                if server_ans[RESPONSE] == 511:
                    text_encoded = server_ans[TEXT].encode('utf-8')
                    hashed_message = hmac.new(passwd_hash_string, text_encoded, 'sha256')
                    hashed_message_digest = hashed_message.digest()

                    hashed_answer = binascii.b2a_base64(hashed_message_digest).decode('ascii')
                    send_message(self.transport, {RESPONSE: 511, TEXT: hashed_answer})
                    self.process_server_ans(get_message(self.transport))

        except (OSError, json.JSONDecodeError):
            logger.critical('Потеряно соединение с сервером!')
            raise ServerError('Потеряно соединение с сервером!')

    # Функция, генерирующая приветственное сообщение для сервера
    def create_presence(self):
        presence_message = {
            ACTION: PRESENCE,
            TIME: time.time(),
            ACCOUNT_NAME: self.username,
            PUBLIC_KEY: self.public_key
        }
        return presence_message

    # Функция обрабатывающяя сообщения от сервера. Ничего не возращает. Генерирует исключение при ошибке.
    def process_server_ans(self, message):
        logger.debug(f'Разбор сообщения от сервера: {message}')

        # Если это подтверждение чего-либо
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                raise ServerError(f'{message[ERROR]}')
            else:
                logger.debug(f'Принят неизвестный код подтверждения {message[RESPONSE]}')

        # Если это сообщение от пользователя добавляем в базу, даём сигнал о новом сообщении
        elif ACTION in message and message[ACTION] == MESSAGE and SENDER in message and RECIPIENT in message \
                and TEXT in message and message[RECIPIENT] == self.username:
            logger.debug(f'Получено сообщение от пользователя {message[SENDER]}:{message[TEXT]}')

            self.new_message.emit(message)


    # Функция обновляющая контакт - лист с сервера
    def contacts_list_update(self):
        logger.debug(f'Запрос контакт листа для пользователся {self.name}')
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.username
        }
        logger.debug(f'Сформирован запрос {req}')
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        logger.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[CONTACTS]:
                self.database.add_contact(contact)
        else:
            logger.error('Не удалось обновить список контактов.')

    # Функция обновления таблицы известных пользователей.
    def user_list_update(self):
        logger.debug(f'Запрос списка известных пользователей {self.username}')
        req = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.database.fill_all_users(ans[ALL_USERS])
        else:
            logger.error('Не удалось обновить список известных пользователей.')

    # Функция сообщающая на сервер о добавлении нового контакта
    def add_contact(self, contact):
        logger.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username,
            CONTACT_NAME: contact
        }
        with socket_lock:
            send_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    def key_request(self, username):
        req = {
            ACTION: PUBLIC_KEY,
            TIME: time.time(),
            CONTACT_NAME: username
        }
        with socket_lock:
            send_message(self.transport, req)
            server_ans = get_message(self.transport)
            if RESPONSE in server_ans and server_ans[RESPONSE] == 200 and PUBLIC_KEY in server_ans:
                return server_ans[PUBLIC_KEY]

    
    def check_contact_is_online(self, contact):
        logger.debug(f'check user is online {contact}')
        req = {
            ACTION: CONTACT_IS_ONLINE,
            TIME: time.time(),
            CONTACT_NAME: contact
        }
        with socket_lock:
            send_message(self.transport, req)
            server_ans = get_message(self.transport)
            if RESPONSE in server_ans and server_ans[RESPONSE] == 200 and CONTACT_IS_ONLINE in server_ans:
                return server_ans[CONTACT_IS_ONLINE]



    # Функция удаления клиента на сервере
    def remove_contact(self, contact):
        logger.debug(f'Удаление контакта {contact}')
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username,
            CONTACT_NAME: contact
        }
        with socket_lock:
            send_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    # Функция закрытия соединения, отправляет сообщение о выходе.
    def transport_shutdown(self):
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
        logger.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    # Функция отправки сообщения на сервер
    def send_message(self, contact_name, message):
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            RECIPIENT: contact_name,
            TIME: time.time(),
            TEXT: message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with socket_lock:
            send_message(self.transport, message_dict)
            self.process_server_ans(get_message(self.transport))
            logger.info(f'Отправлено сообщение для пользователя {contact_name}')

    def run(self):
        logger.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # если не сделать тут задержку, то отправка может достаточно долго ждать освобождения сокета.
            time.sleep(1)
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        logger.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    logger.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                # Если сообщение получено, то вызываем функцию обработчик:
                else:
                    logger.debug(f'Принято сообщение с сервера: {message}')
                    self.process_server_ans(message)
                finally:
                    self.transport.settimeout(5)