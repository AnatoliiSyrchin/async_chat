"""
Start dialog module
user should enter his username and password
or register himself
If everything Ok - user moved to main window
"""
import binascii
import hashlib
import json
import logging
import time
from socket import socket, AF_INET, SOCK_STREAM

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel, qApp, QMessageBox
from PyQt5.QtCore import Qt

from client_part.common.utils import send_message, get_message
from client_part.common.variables import (REGISTER, PASSWORD_HASH, ACTION, TIME, ACCOUNT_NAME,
                                       RESPONSE, ERROR, CHECK_NAME)
import client_part.logs.log_configs.client_log_config

logger = logging.getLogger('app.client')


class UserNameDialog(QDialog):
    """Class for Start dialog"""
    BIG_FONT = QFont("Calibri", 14)

    def __init__(self):
        super().__init__()

        self.messages = QMessageBox()

        self.username_checked = False

        self.setWindowTitle('Login')
        self.setGeometry(200, 200, 200, 440)

        self.login = QLabel('Login', self)
        self.login.setAlignment(Qt.AlignCenter)
        self.login.setGeometry(10, 10, 180, 30)
        self.login.setFont(self.BIG_FONT)

        self.label = QLabel('Enter your name', self)
        self.label.setGeometry(10, 40, 180, 20)

        self.client_name = QLineEdit(self)
        self.client_name.setText('user_1')
        self.client_name.setGeometry(10, 60, 180, 25)

        self.password = QLabel('Enter your password', self)
        self.password.setGeometry(10, 90, 180, 20)

        self.client_password = QLineEdit(self)
        self.client_password.setText('123456')
        self.client_password.setGeometry(10, 110, 180, 25)

        self.btn_ok = QPushButton('Start', self)
        self.btn_ok.setGeometry(10, 145, 180, 25)
        self.btn_ok.clicked.connect(self.click)

        self.register = QLabel('Not registered?', self)
        self.register.setAlignment(Qt.AlignCenter)
        self.register.setFont(self.BIG_FONT)
        self.register.setGeometry(10, 180, 180, 30)

        self.reg_label = QLabel('Enter your name', self)
        self.reg_label.setGeometry(10, 210, 180, 20)

        self.reg_client_name = QLineEdit(self)
        self.reg_client_name.setText('user_1')
        self.reg_client_name.setGeometry(10, 230, 180, 25)

        self.reg_password = QLabel('Enter your password', self)
        self.reg_password.setGeometry(10, 260, 180, 20)

        self.reg_client_password = QLineEdit(self)
        self.reg_client_password.setText('123456')
        self.reg_client_password.setGeometry(10, 280, 180, 25)

        self.reg_password_conf = QLabel('Confirm your password', self)
        self.reg_password_conf.setGeometry(10, 310, 180, 20)

        self.reg_client_password_conf = QLineEdit(self)
        self.reg_client_password_conf.setText('123456')
        self.reg_client_password_conf.setGeometry(10, 330, 180, 25)

        self.btn_reg = QPushButton('register', self)
        self.btn_reg.setGeometry(10, 365, 180, 25)
        self.btn_reg.clicked.connect(self.click_register)

        self.btn_cancel = QPushButton('Exit', self)
        self.btn_cancel.setGeometry(10, 400, 180, 25)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    def click(self):
        """method to handle click on start button"""
        temp_sock = socket(AF_INET, SOCK_STREAM)
        temp_sock.connect(('localhost', 7000))

        message = {
            ACTION: CHECK_NAME,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name.text(),
        }
        try:
            send_message(temp_sock, message)
            response = get_message(temp_sock)
        except (OSError, json.JSONDecodeError):
            logger.critical('Lost connection to server!')
            self.messages.critical(self, 'Error', 'Lost connection to server!')
            qApp.exit()

        # analyzing the answer. Yes, right here))
        if RESPONSE in response:
            if response[RESPONSE] == 200:
                temp_sock.close()
                self.username_checked = True
                self.close()
            elif response[RESPONSE] == 400:
                self.messages.critical(
                    self, 'Error', f'{response[ERROR]}')
            elif response[RESPONSE] == 401:
                self.messages.critical(
                    self, 'Error', response[ERROR])
            else:
                self.messages.critical(
                    self, 'Error', f'Unknown response code {response[RESPONSE]}')
        temp_sock.close()

    def click_register(self):
        """
        method to handle click on register button
        compare passwords and sends information to server
        if result is ok:
        sets text in username and password fields
        sets flag to true
        """

        temp_sock = socket(AF_INET, SOCK_STREAM)
        temp_sock.connect(('localhost', 7000))

        if not self.reg_client_name.text():
            self.messages.critical(
                self, 'Error', 'No user name')
            return
        if self.reg_client_password.text() != self.reg_client_password_conf.text():
            self.messages.critical(
                self, 'Error', 'Passwords dont match')
            return
        # if data exists, creating hash and sending message to server
        client_name = self.reg_client_name.text()
        password_text = self.reg_client_password.text()
        passwd_bytes = password_text.encode('utf-8')
        salt = client_name.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)
        password_hash_decoded = passwd_hash_string.decode('ascii')
        message = {
            ACTION: REGISTER,
            TIME: time.time(),
            ACCOUNT_NAME: client_name,
            PASSWORD_HASH: password_hash_decoded
        }
        try:
            send_message(temp_sock, message)
            response = get_message(temp_sock)
        except (OSError, json.JSONDecodeError):
            logger.critical('Lost connection to server!')
            self.messages.critical(
                self, 'Error', 'Lost connection to server!')
            qApp.exit()

        # analyzing the answer
        if RESPONSE in response:
            if response[RESPONSE] == 200:
                self.messages.information(self, 'Ok', 'User successfully registered.')
                self.client_name.setText(client_name)
                self.client_password.setText(password_text)
                temp_sock.close()
                self.username_checked = True
                self.close()
            elif response[RESPONSE] == 400:
                self.messages.critical(
                    self, 'Error', f'{response[ERROR]}')
            elif response[RESPONSE] == 409:
                self.messages.critical(
                    self, 'Error', 'User already exists')
            else:
                self.messages.critical(
                    self, 'Error', f'Unknown response code {response[RESPONSE]}')
        temp_sock.close()


if __name__ == '__main__':
    app = QApplication([])
    dial = UserNameDialog()
    app.exec_()
