import unittest
import sys
from socket import socket
sys.path.append('./')

from common.utils import get_message


class SocketForTests(socket):
    '''
    подмена сокета для тестов
    метод recv возвращает то же значение, которое было передано при создании объекта
    (наследование от socket, просто чтобы IDE не ругалась на неправильный тип) 
    '''
    def __init__(self, message):
        self.message = message

    def recv(self, _):
        return self.message

class TestClient(unittest.TestCase):
    def test_get_message_ok(self):
        '''correct message from server'''
        self.assertEqual(get_message(SocketForTests(b'{"action": "action"}')), {'action': 'action'})

    def test_get_message_not_dict(self):
        '''decoded message is not dict'''
        self.assertRaises(ValueError, get_message, SocketForTests(b'[]'))

    def test_get_message_not_bytes(self):
        '''received message is not bytes'''
        self.assertRaises(ValueError, get_message, SocketForTests({'action': 'action'}))


if __name__ == '__main__':
    unittest.main()
   