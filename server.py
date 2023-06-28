import sys
import socket
import json
import logging
import logs.log_configs.server_log_config

from common.variables import DEFAULT_PORT, MAX_CONNECTIONS, ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR
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
    return {RESPONSE: 400, ERROR: 'Bad Request'}


def main():
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
    
    logger.info(f'Запущен сервер, порт для подключений: {listen_port}, адрес: {listen_address}.')

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        transport.bind((listen_address, listen_port))
    except Exception as error:
        logger.error(error)
        sys.exit(1)

    # Слушаем порт
    transport.listen(MAX_CONNECTIONS)
    while True:
        client, client_address = transport.accept()
        logger.info(f'Установлено соединени с клиентом {client_address}')
        try:
            message_from_cient = get_message(client)
            logger.debug(f'Получили сообщение от клиента{message_from_cient}')
            # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
            response = process_client_message(message_from_cient)
            logger.info(f'Подготовлен ответ клиенту {response}')
            send_message(client, response)
            client.close()
        except (ValueError, json.JSONDecodeError):
            logger.error('Принято некорретное сообщение от клиента.')
            client.close()
        logger.info(f'Соединение с клиентом {client_address} закрывается')


if __name__ == '__main__':
    main()