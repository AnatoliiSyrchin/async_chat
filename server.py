import sys
import socket
import json
import logging
import select
import time
import logs.log_configs.server_log_config

from common.variables import DEFAULT_PORT, MAX_CONNECTIONS, ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, MESSAGE, TEXT, SENDER
from common.utils import get_message, send_message
from common.decorators import log


logger = logging.getLogger('app.server')

@log
def process_client_message(message: dict) -> dict:
    '''
    Обработчик сообщений от клиентов, принимает словарь-сообщение от клиента,
    проверяет корректность, возвращает словарь-ответ для клиента
    :param message:
    :return:
    '''
    
    # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
    if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
        and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
        return {RESPONSE: 200}
    
    if ACTION in message and message[ACTION] == MESSAGE and TIME in message and TEXT in message:
        return {ACTION: MESSAGE, TIME: time.time(), SENDER: message[ACCOUNT_NAME], TEXT: message[TEXT] }
    
    return {RESPONSE: 400, ERROR: 'Bad Request'}
    

@log
def read_requests(r_clients: list, all_clients: list, requests:list):
    for read_waiting_client in r_clients:
        try:
            message_from_cient = get_message(read_waiting_client)
            logger.debug(f'Получили сообщение от клиента{message_from_cient}')
            if ACTION in message_from_cient and message_from_cient[ACTION] == PRESENCE:
                send_message(read_waiting_client, process_client_message(message_from_cient))
            else:
                requests.append((read_waiting_client, message_from_cient))
        except (ValueError, json.JSONDecodeError):
            logger.error('Принято некорретное сообщение от клиента.')
        except ConnectionError:
            all_clients.remove(read_waiting_client)
            logger.info(f'Соединение с клиентом {read_waiting_client} потеряно')


@log
def write_responses(w_clients, all_clients, requests):
    while requests:
        sock, message = requests.pop()
        response = process_client_message(message)
        logger.info(f'Подготовлен ответ клиенту {response}')
        for write_waiting_client in w_clients:
            try:
                send_message(write_waiting_client, response)
            except ConnectionError:
                all_clients.remove(write_waiting_client)
                logger.info(f'Соединение с клиентом {write_waiting_client} потеряно')

@log
def get_server_parameters():
    # пока просто вынес в отдельную функцию, с парсером разберусь позже) наверно
    '''
    Загрузка параметров командной строки,
    если нет параметров, то задаём значения по умоланию.
    Сначала обрабатываем порт:
    server.py -p 8079 -a 192.168.0.102
    :return:
    '''
    
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            logger.debug('Используется порт по умолчанию')
            listen_port = DEFAULT_PORT
            if listen_port < 1024 or listen_port > 65535:
                raise ValueError
    except IndexError:
        logger.critical('После параметра -\'p\' необходимо указать номер порта.')
        # print('После параметра -\'p\' необходимо указать номер порта.')
        sys.exit(1)
    except ValueError:
        logger.critical('В качастве порта может быть указано только число в диапазоне от 1024 до 65535.')
        # print('В качастве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)
    
    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            logger.debug('Адрес не задан, принимаются соединения с любых адресов')
            listen_address = ''
    except IndexError:
        logger.critical('После параметра -\'a\' необходимо указать адрес, который будет слушать сервер.')
        # print('После параметра -\'a\' необходимо указать адрес, который будет слушать сервер.')
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

        read_requests(read_clients, all_clients, requests)
        if requests:
            write_responses(write_clients, all_clients, requests)

if __name__ == '__main__':
    main()