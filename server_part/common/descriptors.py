""" module with descriptors """
import logging
import sys

CALLING_MODULE_NAME = sys.argv[0].split('/')[-1].split('.')[0]
LOGGER = logging.getLogger(f'app.{CALLING_MODULE_NAME}')


class Port:
    """ descriptor that checks if port value is correct """

    def __set_name__(self, instance, name):
        self.name = f'_{name}'

    def __set__(self, instance, value):
        if value < 1024 or value > 65535:
            LOGGER.critical('В качестве порта может быть указано только число в диапазоне от 1024 до 65535',
                            stacklevel=2)
            sys.exit(1)
        setattr(instance, self.name, value)

    def __get__(self, instance, owner):
        value = getattr(instance, self.name)
        return value
