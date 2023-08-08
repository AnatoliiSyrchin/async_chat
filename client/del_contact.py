"""Module to delete contact"""
from logging import getLogger

from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5.QtCore import Qt

logger = getLogger('app.client')


# Диалог выбора контакта для удаления
class DelContactDialog(QDialog):
    """delete contact dialog"""

    def __init__(self, database):
        super().__init__()
        self.database = database

        self.setFixedSize(350, 120)
        self.setWindowTitle('Choose contact to remove:')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Choose contact to remove:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_ok = QPushButton('Delete', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Cancel', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.mu_public_close)

        # заполнитель контактов для удаления
        self.selector.addItems(self.get_sorted_contacts())

    def get_sorted_contacts(self):
        """just method for pylint"""
        return sorted(self.database.get_contacts())

    def mu_public_close(self):
        """just method for pylint"""
        self.close()


if __name__ == '__main__':
    app = QApplication([])
    window = DelContactDialog(None)
    window.show()
    app.exec_()
