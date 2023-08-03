import os
import sys
import traceback
import logging

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)))

# без этих импортов тоже почему-то всё работает
# import logs.log_configs.server_log_config
# import logs.log_configs.client_log_config

CALLING_MODULE_NAME = sys.argv[0].split('/')[-1].split('.')[0]
LOGGER = logging.getLogger(f'app.{CALLING_MODULE_NAME}')


def log(func):
    def wrapper(*args, **kwargs):

        traceback_result = traceback.format_stack()[0].split()
        # изменил получение имени функции, чтобы работало, даже если функция с параметрами
        traceback_func = traceback_result[6].split('(')[0]
        func_module = func.__module__ if func.__module__ != '__main__' else CALLING_MODULE_NAME

        LOGGER.debug(f'Вызов функции {func.__name__} из модуля {func_module} с параметрами {args, kwargs}.'
                     f'Вызов произошел из функции {traceback_func} из модуля {CALLING_MODULE_NAME}.', stacklevel=2)
        
        result = func(*args, **kwargs)

        return result
    return wrapper
