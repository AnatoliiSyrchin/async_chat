import unittest
import sys
sys.path.append('./')

from common.variables import RESPONSE,PRESENCE, ERROR, TIME, USER, ACCOUNT_NAME, ACTION
from server.server import process_client_message


class TestServer(unittest.TestCase):
    err_dict = {RESPONSE: 400, ERROR: 'Bad Request'}
    ok_dict = {RESPONSE: 200}

    # normal message dict:
    # {ACTION: PRESENCE, TIME: 1573760672.167031, USER: {ACCOUNT_NAME: 'Guest'}}

    def test_no_action(self):
        '''no action in message'''
        self.assertEqual(
            process_client_message(
                {TIME: 1573760672.167031, USER: {ACCOUNT_NAME: 'Guest'}}),
                self.err_dict
            )
    
    def test_wrong_action(self):
        '''wrong action in message'''
        self.assertEqual(
            process_client_message(
                {ACTION: 'wrong', TIME: 1573760672.167031, USER: {ACCOUNT_NAME: 'Guest'}}),
                self.err_dict
            )
        
    def test_no_time(self):
        '''no time in message'''
        self.assertEqual(
            process_client_message(
                {ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest'}}),
                self.err_dict
            )
        
    def test_no_user(self):
        '''no user in message'''
        self.assertEqual(
            process_client_message(
                {ACTION: PRESENCE, TIME: 1573760672.167031}),
                self.err_dict
            )
    
    def test_unknown_user(self):
        '''wrong user in message'''
        self.assertEqual(
            process_client_message(
                {ACTION: PRESENCE, TIME: 1573760672.167031, USER: {ACCOUNT_NAME: 'Wrong User'}}),
                self.err_dict
            )
        
    def test_ok_check(self):
        '''correct message'''
        self.assertEqual(
            process_client_message(
                {ACTION: PRESENCE, TIME: 1573760672.167031, USER: {ACCOUNT_NAME: 'Guest'}}),
                self.ok_dict
            )

if __name__ == '__main__':
    unittest.main()
