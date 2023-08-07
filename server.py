"""main server module"""
import argparse
import configparser
import logging
import os
import sys
from threading import Thread, Lock

from PyQt5.QtWidgets import QMessageBox, QApplication

from common.decorators import log
from common.variables import DEFAULT_PORT
from db.server_datebase import ServerStorage
from server.server_gui import MyMainWindow
from server.server_transport import ServerTransport

sys.path.append(os.getcwd())

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


def refresh_tab(window, config, index, server=None):
    if index == 0:
        window.tab_1.table.setModel(server.create_users_model())
        window.tab_1.table.resizeColumnsToContents()
        window.tab_1.table.resizeRowsToContents()

    if index == 1:
        window.tab_2.table.setModel(server.create_history_model())
        window.tab_2.table.resizeColumnsToContents()
        window.tab_2.table.resizeRowsToContents()

    if index == 2:
        server_config(window.tab_3, config, server)


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


def main():
    config = configparser.ConfigParser()

    dir_path = os.getcwd()
    config.read(f"{dir_path}/server/{'server.ini'}")
    listen_address, listen_port = get_server_parameters(config['SETTINGS']['Default_port'],
                                                        config['SETTINGS']['Listen_Address'])

    path_to_base_dir = config['SETTINGS']['Database_path'] or os.path.join(dir_path, 'db')
    path = os.path.join(path_to_base_dir, config['SETTINGS']['Database_file'])
    server_base = ServerStorage(path)

    server = ServerTransport(listen_address, listen_port, server_base)
    server.init_server()
    server_thread = Thread(target=server.main_loop)
    server_thread.daemon = True
    server_thread.start()

    server_app = QApplication(sys.argv)
    main_window = MyMainWindow()

    main_window.statusBar().showMessage('Server Working')

    # refresh widget on active tab
    refresh_tab(main_window, config, main_window.tab_widget.currentIndex(), server)

    main_window.show()

    main_window.tab_1.refresh_button.clicked.connect(
        lambda: refresh_tab(main_window, config, main_window.tab_widget.currentIndex(), server))

    main_window.tab_2.refresh_button.clicked.connect(
        lambda: refresh_tab(main_window, config, main_window.tab_widget.currentIndex(), server))

    main_window.tab_widget.currentChanged.connect(
        lambda: refresh_tab(main_window, config, main_window.tab_widget.currentIndex(), server))

    # Start GUI
    server_app.exec_()


if __name__ == '__main__':
    main()