# Порт по умолчанию для сетевого ваимодействия
DEFAULT_PORT = 7777

# IP адрес по умолчанию для подключения клиента
DEFAULT_IP_ADDRESS = '127.0.0.1'
# DEFAULT_IP_ADDRESS = '192.168.238.1'

# Максимальная очередь подключений
MAX_CONNECTIONS = 5

# Максимальная длинна сообщения в байтах
MAX_PACKAGE_LENGTH = 1024

# Кодировка проекта
ENCODING = 'utf-8'

# Протокол JIM основные ключи:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'

# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
MESSAGE = 'message'
ERROR = 'error'
TEXT = 'text'
SENDER = 'sender'
RECIPIENT = 'recipient'
EXIT = 'exit'
GET_CONTACTS = 'get_contacts'
ALL_USERS = 'all_users'
CONTACTS = 'contacts'
ADD_CONTACT = 'add_contact'
REMOVE_CONTACT = 'remove_contact'
USERS_REQUEST = 'users_request'
CONTACT_NAME = 'contact_name'