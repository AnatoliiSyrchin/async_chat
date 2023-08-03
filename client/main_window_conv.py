# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'client.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!
import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QRect, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QWidget, QTextEdit, QListView, QMenuBar, \
    QMenu, QStatusBar


class UiMainClientWindow(object):
    
    def __init__(self, main_client_window):
        # main_client_window.setObjectName("main_client_window")
        main_client_window.resize(756, 534)
        main_client_window.setMinimumSize(QSize(756, 534))
        main_client_window.setWindowTitle('Chat')

        self.centralwidget = QWidget(main_client_window)
        # self.centralwidget.setObjectName("centralwidget")

        self.label_contacts = QLabel("Contacts list", self.centralwidget)
        self.label_contacts.setGeometry(10, 0, 101, 16)
        # self.label_contacts.setObjectName("label_contacts")

        self.btn_add_contact = QPushButton("Add contact", self.centralwidget)
        self.btn_add_contact.setGeometry(10, 450, 121, 31)
        # self.btn_add_contact.setObjectName("btn_add_contact")

        self.btn_remove_contact = QPushButton("Remove contact", self.centralwidget)
        self.btn_remove_contact.setGeometry(140, 450, 121, 31)
        # self.btn_remove_contact.setObjectName("btn_remove_contact")

        self.label_history = QLabel("History", self.centralwidget)
        self.label_history.setGeometry(300, 0, 391, 21)
        # self.label_history.setObjectName("label_history")

        self.text_message = QTextEdit("Enter message", self.centralwidget)
        self.text_message.setGeometry(300, 360, 441, 71)
        # self.text_message.setObjectName("text_message")

        self.label_new_message = QLabel("New message", self.centralwidget)
        self.label_new_message.setGeometry(300, 330, 450, 16) # Правка тут
        # self.label_new_message.setObjectName("label_new_message")

        self.list_contacts = QListView(self.centralwidget)
        self.list_contacts.setGeometry(10, 20, 251, 411)
        # self.list_contacts.setObjectName("list_contacts")

        self.list_messages = QListView(self.centralwidget)
        self.list_messages.setGeometry(300, 20, 441, 301)
        # self.list_messages.setObjectName("list_messages")

        self.btn_send = QPushButton("Send", self.centralwidget)
        self.btn_send.setGeometry(610, 450, 131, 31)
        # self.btn_send.setObjectName("btn_send")

        self.btn_clear = QPushButton("Clear", self.centralwidget)
        self.btn_clear.setGeometry(460, 450, 131, 31)
        # self.btn_clear.setObjectName("btn_clear")

        main_client_window.setCentralWidget(self.centralwidget)

        self.menubar = QMenuBar(main_client_window)
        self.menubar.setGeometry(0, 0, 756, 21)
        # self.menubar.setObjectName("menubar")

        self.menu = QMenu("File", self.menubar)
        # self.menu.setObjectName("menu")

        self.menu_2 = QMenu("Contacts", self.menubar)
        # self.menu_2.setObjectName("menu_2")

        main_client_window.setMenuBar(self.menubar)

        self.statusBar = QStatusBar(main_client_window)
        # self.statusBar.setObjectName("statusBar")
        main_client_window.setStatusBar(self.statusBar)

        self.menu_exit = QtWidgets.QAction("Exit", main_client_window)
        # self.menu_exit.setObjectName("menu_exit")

        self.menu_add_contact = QtWidgets.QAction("Add contact", main_client_window)
        # self.menu_add_contact.setObjectName("menu_add_contact")

        self.menu_del_contact = QtWidgets.QAction("Delete contact", main_client_window)
        # self.menu_del_contact.setObjectName("menu_del_contact")

        self.menu.addAction(self.menu_exit)
        self.menu_2.addAction(self.menu_add_contact)
        self.menu_2.addAction(self.menu_del_contact)
        self.menu_2.addSeparator()

        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())

        # self.retranslateUi(main_client_window)
        self.btn_clear.clicked.connect(self.text_message.clear)
        # QtCore.QMetaObject.connectSlotsByName(main_client_window)
    #
    # def retranslateUi(self, main_client_window):
    #     _translate = QtCore.QCoreApplication.translate
    #     main_client_window.setWindowTitle(_translate("main_client_window", "Чат Программа alpha release"))
    #     self.label_contacts.setText(_translate("main_client_window", "Список контактов:"))
    #     self.btn_add_contact.setText(_translate("main_client_window", "Добавить контакт"))
    #     self.btn_remove_contact.setText(_translate("main_client_window", "Удалить контакт"))
    #     self.label_history.setText(_translate("main_client_window", "История сообщений:"))
    #     self.label_new_message.setText(_translate("main_client_window", "Введите новое сообщение:"))
    #     self.btn_send.setText(_translate("main_client_window", "Отправить сообщение"))
    #     self.btn_clear.setText(_translate("main_client_window", "Очистить поле"))
    #     self.menu.setTitle(_translate("main_client_window", "Файл"))
    #     self.menu_2.setTitle(_translate("main_client_window", "Контакты"))
    #     self.menu_exit.setText(_translate("main_client_window", "Выход"))
    #     self.menu_add_contact.setText(_translate("main_client_window", "Добавить контакт"))
    #     self.menu_del_contact.setText(_translate("main_client_window", "Удалить контакт"))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Breeze')
    ex = QMainWindow()
    ex.ui = UiMainClientWindow(ex)
    ex.show()
    sys.exit(app.exec_())
    