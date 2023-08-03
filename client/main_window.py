
import sys
import os
import logging
import base64

from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication, QListView
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, QEvent, Qt

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)))

from client.main_window_conv import UiMainClientWindow
from client.add_contact import AddContactDialog
from client.del_contact import DelContactDialog
from db.client_datebase import ClientStorage
from client.transport import ClientTransport
from common.variables import SENDER, TEXT
# from client.start_dialog import UserNameDialog
from common.errors import ServerError
import logs.log_configs.server_log_config

logger = logging.getLogger('app.client')


# Класс основного C
class ClientMainWindow(QMainWindow):
    def __init__(self, database, transport, rsa_key):
        super().__init__()
        # основные переменные
        self.database = database
        self.transport = transport

        # Загружаем конфигурацию окна из дизайнера
        self.ui = UiMainClientWindow(self)

        # Кнопка "Выход"
        self.ui.menu_exit.triggered.connect(qApp.exit)

        # Кнопка отправить сообщение
        self.ui.btn_send.clicked.connect(self.send_message)

        # "добавить контакт"
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)

        # Удалить контакт
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)

        # Дополнительные требующиеся атрибуты
        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.current_chat_key = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)
        self.decryptor = PKCS1_OAEP.new(rsa_key)

        # Даблклик по листу контактов отправляется в обработчик
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    # Деактивировать поля ввода
    def set_disabled_input(self):
        # Надпись  - получатель.
        self.ui.label_new_message.setText('Duble click on users name in contact list.')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        # Поле ввода и кнопка отправки неактивны до выбора получателя.
        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

        self.encryptor = None
        self.current_chat = None
        self.current_chat_key = None

    def history_list_update(self):
        
        history_list = sorted(
            self.database.get_message_history(contact=self.current_chat),
            key=lambda message: message.date)
        
        # create gistory model if not exists
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        
        # clear history
        self.history_model.clear()

        # Take 20 last messages or less
        length = len(history_list)
        start_index = 0
        if length > 20:
            start_index = length - 20

        # Filling model with data. Incomming are light pink colored, outcoming - light green.
        for i in range(start_index, length):
            item = history_list[i]
            if item.direction == 'in':
                mess = QStandardItem(f'Incoming at {item.date.strftime("%d.%m.%Y %H:%M")}:\n {item.message}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(f'Outcoming at {item.date.strftime("%d.%m.%Y %H:%M")}:\n {item.message}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    # Function for duble click signal from contact
    def select_active_user(self):
        # Pick choosen user from qlistview
        contact_name = self.ui.list_contacts.currentIndex().data()
        result = self.transport.check_contact_is_online(contact_name)
        if result:
            self.current_chat = self.ui.list_contacts.currentIndex().data()
            # call fucnction that sets the active user
            self.set_active_user()
        else:
            self.messages.critical(self, 'Error', f'user {contact_name} is offline')

    # fucnction that sets the active user
    def set_active_user(self):
        self.current_chat_key = self.transport.key_request(self.current_chat)
        if self.current_chat_key:
            self.encryptor = PKCS1_OAEP.new(RSA.import_key(self.current_chat_key))

        if not self.current_chat_key:
            self.messages.warning(self, 'Ошибка', 'Для выбранного пользователя нет ключа шифрования.')
            return

        # Activating interface for messages
        self.ui.label_new_message.setText(f'Enter message for {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)

        # fill history for the active user
        self.history_list_update()

    # Function that updates contact list
    def clients_list_update(self):
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    # Function that calling adding contact dialog
    def add_contact_window(self):
        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.database)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    # Function-handler of adding contact, gets contact from selector, and calling "add_contact" function 
    def add_contact_action(self, item):
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    # Function sends information about contact ot server and adds it to base
    def add_contact(self, new_contact):
        try:
            self.transport.add_contact(new_contact)
        except ServerError as err:
            self.messages.critical(self, 'Server error', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Error', 'Lost connection with server!')
                self.close()
            self.messages.critical(self, 'Error', 'Connection timeout!')
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            logger.info(f'Added contact {new_contact}')
            self.messages.information(self, 'Ok', 'Contact added.')

    # Function that calls remove contact dialog
    def delete_contact_window(self):
        global remove_dialog
        remove_dialog = DelContactDialog(self.database)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    # Function-handler of contact deleting, gets contact from selector, sends information to server,
    # deletes contact from base and updates contacts list
    def delete_contact(self, item):
        selected = item.selector.currentText()
        try:
            self.transport.remove_contact(selected)
        except ServerError as err:
            self.messages.critical(self, 'Server error', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Error', 'Lost connection with server!')
                self.close()
            self.messages.critical(self, 'Error', 'Connection timeout!')
        else:
            self.database.del_contact(selected)
            self.clients_list_update()
            logger.info(f'Contact removed {selected}')
            self.messages.information(self, 'Ok', 'Contact removed.')
            item.close()
            # Deactivate interface if contact was active contact.
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    # Function sending message to server, saving to datebase and updating history list
    def send_message(self):
        # getting test from field, and clearing it
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        logger.debug(f'sending message {self.current_chat}, {message_text}')

        if not message_text:
            return
        
        message_text_encrypted = self.encryptor.encrypt(message_text.encode('utf8'))
        message_text_encrypted_base64 = base64.b64encode(message_text_encrypted)

        try:
            self.transport.send_message(self.current_chat, message_text_encrypted_base64.decode('ascii'))
            pass
        except ServerError as err:
            self.messages.critical(self, 'Error', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Error', 'Lost connection with server!')
                self.close()
            self.messages.critical(self, 'Error in sending message', 'Connection timeout!')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Error', 'Lost connection with server!')
            self.close()
        else:
            self.database.save_message(self.current_chat, 'out', message_text)
            self.history_list_update()

    # New message receiving slot
    @pyqtSlot(dict)
    def message(self, message):

        sender = message[SENDER]
        text = message[TEXT]
        message_text_decoded = base64.b64decode(text)
        try:
            message_text_decrypted = self.decryptor.decrypt(message_text_decoded).decode('utf-8')
        except (ValueError, TypeError):
            self.messages.warning(
                self, 'Ошибка', 'Не удалось декодировать сообщение.')
            return

        self.database.save_message(sender , 'in' , message_text_decrypted)


        if sender == self.current_chat:
            self.history_list_update()
        else:
            # Check if user in our contacts:
            if self.database.check_contact(sender):
                # Asking to open chat with contact 
                if self.messages.question(self, 'New message',
                                          f'New message from {sender} received, do you want to open chat?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                # Раз нету,спрашиваем хотим ли добавить юзера в контакты.
                if self.messages.question(self, 'New message',
                                          f'New message from {sender} received. \n' 
                                          f'This user is not in your contacts. Do you want to add it and open chat?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.set_active_user()

    @pyqtSlot()
    def connection_lost(self):
        self.messages.warning(self, 'Lost connection', 'Lost connection with server. ')
        self.close()

    def make_connection(self, trans_obj):
        logger.debug(f'make connection {trans_obj}')
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Breeze')
    
    base = ClientStorage(prefix='test_')
    sock = ClientTransport(7000, '127.0.0.1', base, 'test_client')

    ex = ClientMainWindow(base, sock)
    # ex.ui = UiMainClientWindow(ex)
    ex.show()
    sys.exit(app.exec_())
