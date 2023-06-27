import sys
import socket
import json
import time
import logging

import log.log_configs.client_log_config
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT
from common.utils import get_message, send_message

logger = logging.getLogger('app.client')

def create_presence (account_name: str = 'Guest') -> dict:
    # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
    out = {ACTION: PRESENCE, TIME: time.time(), USER: {ACCOUNT_NAME: account_name } }
    return out

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
    
def main():
    '''Загружаем параметы коммандной строки'''
    # cLient.py 192.168.57.33 8079
    # server.py -p 8079 -a 192.168.57.33
    try:
        server_address = sys.argv[1]
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
    logger.info(f'Запущен клиент с парамертами: адрес сервера: {server_address}, порт: {server_port}')

    #  Инициализация сокета и обмен
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
        message_to_server = create_presence()
        logger.info(f'Создано сообщение для сервера: {message_to_server}')
        send_message(transport, message_to_server)
        try:
            answer = process_ans(get_message(transport))
            logger.info(f'Получен ответ от сервера: {answer}')
            # print(answer)
        except (ValueError, json.JSONDecodeError):
            logger.error('He удалось декодировать сообщение сервера.')
            # print('He удалось декодировать сообщение сервера.')
    except Exception as error:
        logger.critical(f'somethong went wrong: {error}')


if __name__ == '__main__':
    main()

# словарь - json-строка - байты
