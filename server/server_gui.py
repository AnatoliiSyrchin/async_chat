import os
import sys

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QAction, QTabWidget, QWidget, QApplication, \
    QVBoxLayout, QTableView, QLabel, QPushButton, QLineEdit, qApp, QFileDialog

from db.server_datebase import ServerStorage

global select_base_dialog


class MyMainWindow(QMainWindow):

    def __init__(self):
        super(MyMainWindow, self).__init__()

        self.setGeometry(500, 500, 900, 400)
        self.setWindowTitle('Main window')

        self.exit_action = QAction('Exit', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.triggered.connect(qApp.quit)

        self.central_widget = QWidget(self)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget(self.central_widget)
        self.tab_widget.setTabShape(QTabWidget.Triangular)

        self.tab_1 = UsersList(self.tab_widget)
        self.tab_widget.addTab(self.tab_1, "Users list")

        self.tab_2 = HistoryList(self.tab_widget)
        self.tab_widget.addTab(self.tab_2, "History list")

        self.tab_3 = ServerSettings()
        self.tab_widget.addTab(self.tab_3, "Server config")

        self.main_layout.addWidget(self.tab_widget)

        self.setCentralWidget(self.central_widget)

        self.toolbar = self.addToolBar('toolbar')
        self.toolbar.addAction(self.exit_action)

        self.statusBar()


class UsersList(QWidget):

    def __init__(self, parent=None):
        super(UsersList, self).__init__(parent=parent)

        self.layout = QVBoxLayout(self)

        self.refresh_button = QPushButton('Refresh table')
        self.table = QTableView(self)

        self.layout.addWidget(self.table)
        self.layout.addWidget(self.refresh_button)


class HistoryList(QWidget):

    def __init__(self, parent=None):
        super(HistoryList, self).__init__(parent=parent)

        self.layout = QVBoxLayout(self)

        self.refresh_button = QPushButton('Refresh table')
        self.table = QTableView(self)

        self.layout.addWidget(self.table)
        self.layout.addWidget(self.refresh_button)


class ServerSettings(QWidget):
    FONT = QFont("Calibri", 10)

    def __init__(self, parent=None):
        super(ServerSettings, self).__init__(parent=parent)

        # self.layout = QVBoxLayout()

        self.select_base_text = QLabel('Enter location of the data base', self)
        self.select_base_text.setGeometry(20, 20, 220, 20)
        self.select_base_text.setFont(self.FONT)

        self.select_base_path = QLineEdit(self)
        self.select_base_path.setGeometry(20, 40, 250, 20)
        self.select_base_path.setFont(self.FONT)

        self.select_base_button = QPushButton('Select...', self)
        self.select_base_button.setGeometry(280, 39, 100, 22)
        self.select_base_button.setFont(self.FONT)

        self.select_base_button.clicked.connect(self.open_file_dialog)

        self.filename = QLabel('Enter data base filename', self)
        self.filename.setGeometry(20, 80, 180, 20)
        self.filename.setFont(self.FONT)

        self.filename_field = QLineEdit(self)
        self.filename_field.setGeometry(210, 80, 170, 20)
        self.filename_field.setFont(self.FONT)

        self.ip_text = QLabel('Enter IP address', self)
        self.ip_text.setGeometry(20, 120, 180, 20)
        self.ip_text.setFont(self.FONT)

        self.ip_field = QLineEdit(self)
        self.ip_field.setGeometry(210, 120, 170, 20)
        self.ip_field.setFont(self.FONT)

        self.port_text = QLabel('Enter Port', self)
        self.port_text.setGeometry(20, 160, 180, 20)
        self.port_text.setFont(self.FONT)

        self.port_field = QLineEdit(self)
        self.port_field.setGeometry(210, 160, 170, 20)
        self.port_field.setFont(self.FONT)

        self.save_button = QPushButton('Save', self)
        self.save_button.setGeometry(280, 200, 100, 22)

    @pyqtSlot()
    def open_file_dialog(self):
        dialog = QFileDialog(self)
        path = dialog.getExistingDirectory()
        # path = path.replace('/', '\\')
        self.select_base_path.setText(path)


if __name__ == '__main__':
    server_base = ServerStorage(f'{os.path.dirname(os.path.realpath(__file__))}/db/test_server.db')
    server_base.user_login('alesha', '127.0.0.1', 7000)
    server_base.user_login('masha', '127.0.0.2', 5000)

    app = QApplication(sys.argv)
    # display_size = app.primaryScreen().size()
    ex = MyMainWindow()
    ex.show()
    sys.exit(app.exec_())
