import argparse
import sys
import os
import logging
import threading

from PyQt5.QtWidgets import QApplication

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)))

from common.variables import *
from common.errors import ServerError
from common.decorators import log
from db.client_datebase import ClientStorage
from client.transport import ClientTransport
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
import logs.log_configs.client_log_config

logger = logging.getLogger('app.client')


@log
def get_client_parameters() -> tuple:
    """Getting parameters from command line"""
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
    if server_port < 1024 or server_port > 65535:
        logger.critical('В качестве порта может быть указано только число в диапазоне от 1024 до 65535')
        sys.exit(1)
    return server_address, server_port, client_name


def main():
    server_address, server_port, client_name = get_client_parameters()
    client_app = QApplication(sys.argv)

    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        # If user entered ok, then saving his name adn closing dialog, else - exit
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            sys.exit(0)

    client_database = ClientStorage(prefix=f'{client_name}_')

    try:
        transport = ClientTransport(server_port, server_address, client_database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()
    
    client_window = ClientMainWindow(client_database, transport)
    client_window.make_connection(transport)
    client_window.setWindowTitle(f'{client_name}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()


if __name__ == '__main__':
    main()
