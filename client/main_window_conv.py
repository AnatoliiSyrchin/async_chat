"""module of main window clients interface converted from PyQt designer"""

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton, QLabel, QWidget, QTextEdit, QListView, QMenuBar, \
    QMenu, QStatusBar


class UiMainClientWindow:
    """main window clients interface"""

    def __init__(self, main_client_window):
        main_client_window.resize(756, 534)
        main_client_window.setMinimumSize(QSize(756, 534))
        main_client_window.setWindowTitle('Chat')

        self.central_widget = QWidget(main_client_window)

        self.label_contacts = QLabel("Contacts list", self.central_widget)
        self.label_contacts.setGeometry(10, 0, 101, 16)

        self.btn_add_contact = QPushButton("Add contact", self.central_widget)
        self.btn_add_contact.setGeometry(10, 450, 121, 31)

        self.btn_remove_contact = QPushButton("Remove contact", self.central_widget)
        self.btn_remove_contact.setGeometry(140, 450, 121, 31)

        self.label_history = QLabel("History", self.central_widget)
        self.label_history.setGeometry(300, 0, 391, 21)

        self.text_message = QTextEdit("Enter message", self.central_widget)
        self.text_message.setGeometry(300, 360, 441, 71)

        self.label_new_message = QLabel("New message", self.central_widget)
        self.label_new_message.setGeometry(300, 330, 450, 16)  # Правка тут

        self.list_contacts = QListView(self.central_widget)
        self.list_contacts.setGeometry(10, 20, 251, 411)

        self.list_messages = QListView(self.central_widget)
        self.list_messages.setGeometry(300, 20, 441, 301)

        self.btn_send = QPushButton("Send", self.central_widget)
        self.btn_send.setGeometry(610, 450, 131, 31)

        self.btn_clear = QPushButton("Clear", self.central_widget)
        self.btn_clear.setGeometry(460, 450, 131, 31)

        main_client_window.setCentralWidget(self.central_widget)

        self.menubar = QMenuBar(main_client_window)
        self.menubar.setGeometry(0, 0, 756, 21)

        self.menu = QMenu("File", self.menubar)

        self.menu_2 = QMenu("Contacts", self.menubar)

        main_client_window.setMenuBar(self.menubar)

        self.status_bar = QStatusBar(main_client_window)
        main_client_window.setStatusBar(self.status_bar)

        self.menu_exit = QtWidgets.QAction("Exit", main_client_window)

        self.menu_add_contact = QtWidgets.QAction("Add contact", main_client_window)

        self.menu_del_contact = QtWidgets.QAction("Delete contact", main_client_window)

        self.menu.addAction(self.menu_exit)
        self.menu_2.addAction(self.menu_add_contact)
        self.menu_2.addAction(self.menu_del_contact)
        self.menu_2.addSeparator()

        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())

        self.btn_clear.clicked.connect(self.text_message.clear)
