"""main client module"""
import argparse
import sys
import os
import logging

from PyQt5.QtWidgets import QApplication
from Crypto.PublicKey import RSA

sys.path.append(os.getcwd())

from common.variables import DEFAULT_IP_ADDRESS, DEFAULT_PORT
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

    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('--pswd', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    password = namespace.pswd
    if server_port < 1024 or server_port > 65535:
        logger.critical('В качестве порта может быть указано только число в диапазоне от 1024 до 65535')
        sys.exit(1)
    return server_address, server_port, client_name, password


def main():
    """main client method"""
    server_address, server_port, client_name, client_password = get_client_parameters()
    client_app = QApplication(sys.argv)

    if not (client_name and client_password):
        start_dialog = UserNameDialog()
        client_app.exec_()
        # If user pressed ok, then saving his name and password, else - exit
        if start_dialog.username_checked:
            client_name = start_dialog.client_name.text()
            client_password = start_dialog.client_password.text()
            logger.debug(f'username_checked {client_name} {client_password}')
        else:
            sys.exit(0)

    client_database = ClientStorage(prefix=f'{client_name}_')

    dir_path = os.getcwd()
    if not os.path.exists('client/keys'):
        os.mkdir('client/keys')
    key_file = os.path.join(dir_path, f'client/keys/{client_name}.key')
    if not os.path.exists(key_file):
        rsa_key = RSA.generate(2048)
        with open(key_file, 'wb') as f_key:
            f_key.write(rsa_key.export_key())
    else:
        with open(key_file, 'rb') as f_key:
            rsa_key = RSA.import_key(f_key.read())

    try:
        print(f'Client {client_name}')
        transport = ClientTransport(server_port, server_address, client_database, client_name, client_password, rsa_key)
    except ServerError:
        sys.exit(1)

    transport.daemon = True
    transport.start()

    del start_dialog

    client_window = ClientMainWindow(client_database, transport, rsa_key)
    client_window.make_connection(transport)
    client_window.setWindowTitle(f'{client_name}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()


if __name__ == '__main__':
    main()
