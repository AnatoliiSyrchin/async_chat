import logging
import os

logger = logging.getLogger('app.client')

log_file = os.path.abspath(os.path.join(os.getcwd(), os.path.pardir)) + '/log_files/app.client.log'

formatter = logging.Formatter('%(asctime)s  %(levelname)-8s  %(module)-10s %(message)s')

file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    logger.info('test write log')
    logger.critical('critical write log')
