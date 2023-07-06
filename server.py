import sys
import socket
import json
import logging
import select
import argparse

import logs.log_configs.server_log_config
from common.variables import DEFAULT_PORT, MAX_CONNECTIONS, ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME,\
    RESPONSE, ERROR, MESSAGE, TEXT, SENDER, RECIPIENT, EXIT
from common.utils import get_message, send_message
from common.decorators import log


logger = logging.getLogger('app.server')


@log
def process_client_message(sock: socket.socket, all_clients: list, message: dict, names: dict, requests: list):
    """
    Обработчик сообщений от клиентов, принимает словарь-сообщение от клиента,
    проверяет корректность, возвращает словарь-ответ для клиента
    :param message:
    :param names:
    :param all_clients:
    :param requests:
    :param sock:
    :return:
    """
    # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}

    if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
            and USER in message and ACCOUNT_NAME in message[USER]:

        if message[USER][ACCOUNT_NAME] not in names.keys():
            names[message[USER][ACCOUNT_NAME]] = sock
            send_message(sock, {RESPONSE: 200})
        else:
            logger.info('RESPONSE: 400, ERROR: "account name already exists"')
            send_message(sock, {RESPONSE: 400, ERROR: 'account name already exists'})
            all_clients.remove(sock)
            sock.close()
        return

    elif ACTION in message and message[ACTION] == EXIT and TIME in message and \
            USER in message and ACCOUNT_NAME in message[USER]:
        del names[message[USER][ACCOUNT_NAME]]
        all_clients.remove(sock)
        sock.close()
        return

    elif ACTION in message and message[ACTION] == MESSAGE and TIME in message and \
            SENDER in message and RECIPIENT in message and TEXT in message:
        requests.append((sock, message))
        return message

    else:
        send_message(sock, {RESPONSE: 400, ERROR: 'Bad Request'})
        return
    

@log
def read_requests(r_clients: list, all_clients: list, names: dict, requests: list):
    for read_waiting_client in r_clients:
        try:
            message_from_client = get_message(read_waiting_client)
            logger.info(f'Получили сообщение от клиента {read_waiting_client.getpeername()} {message_from_client}')
            process_client_message(read_waiting_client, all_clients, message_from_client, names, requests)
        except (ValueError, json.JSONDecodeError):
            logger.error('Принято некорректное сообщение от клиента.')
        except ConnectionError:
            all_clients.remove(read_waiting_client)
            logger.info(f'Соединение с клиентом {read_waiting_client} потеряно')


@log
def write_responses(w_clients, all_clients, names, requests):
    while requests:
        sock, message = requests.pop()
        logger.error(f'pop {message}')
        recipient = message[RECIPIENT]
        if recipient in names:
            recipient_socket = names[recipient]
            try:
                send_message(recipient_socket, message)
            except ConnectionError:
                all_clients.remove(recipient_socket)
                del names[recipient]
                logger.info(f'Соединение с клиентом {recipient} потеряно')
        else:
            send_message(sock, {RESPONSE: 400, ERROR: f'account name {recipient} does not exist'})
            logger.info(f'Клиент с именем {recipient} не существует')


@log
def get_server_parameters():
    """
    Загрузка параметров командной строки,
    если нет параметров, то задаём значения по умоланию.
    :return:
    """
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', '--address', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_port = namespace.port
    listen_address = namespace.address

    if listen_port < 1024 or listen_port > 65535:
        logger.critical('В качестве порта может быть указано только число в диапазоне от 1024 до 65535')
        sys.exit(1) 

    return listen_port, listen_address


def main():
    
    listen_port, listen_address = get_server_parameters()

    logger.info(f'Запущен сервер, порт для подключений: {listen_port}, адрес: {listen_address}.')

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        transport.bind((listen_address, listen_port))
    except Exception as error:
        logger.error(error)
        sys.exit(1)

    # Слушаем порт
    transport.listen(MAX_CONNECTIONS)
    transport.settimeout(1)

    all_clients = []
    requests = []

    names = {}

    while True:
        try:
            client, client_address = transport.accept()
            logger.info(f'Установлено соединение с клиентом {client_address}')
            all_clients.append(client)
        except OSError as err:
            pass

        read_clients = []
        write_clients = []
        wait = 5
        try:
            read_clients, write_clients, [] = select.select(all_clients, all_clients, [], wait)
        except:
            pass

        read_requests(read_clients, all_clients, names, requests)
        if requests:
            write_responses(write_clients, all_clients, names, requests)


if __name__ == '__main__':
    main()
