import unittest
import sys
sys.path.append('/')

from server_part.common import RESPONSE, ERROR, TIME, USER, ACCOUNT_NAME, ACTION
from client_part.client import create_presence, process_ans


class TestClient(unittest.TestCase):
    def test_create_presence(self):
        '''correct presence message'''
        test = create_presence()
        test[TIME] = 1
        self.assertEqual(test, {ACTION: 'presence', TIME: 1, USER: {ACCOUNT_NAME: 'Guest'}})

    def test_200_ans(self):
        '''correct server response'''
        self.assertEqual(process_ans({RESPONSE: 200}), '200 : OK')
    
    def test_400_ans(self):
        '''server response with error'''
        self.assertEqual(process_ans({RESPONSE: 400, ERROR: 'Bad Request'}), '400 : Bad Request')

    def test_no_response(self):
        '''no server response'''
        self.assertRaises(ValueError, process_ans, {ERROR: 'Bad Request'})

if __name__ == '__main__':
    unittest.main()
    