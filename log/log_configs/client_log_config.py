import logging

logger = logging.getLogger('app.client')

formatter = logging.Formatter('%(asctime)s  %(levelname)-8s  %(module)-10s %(message)s')

file_handler = logging.FileHandler('log/log_files/app.client.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    logger.info('test write log')
    logger.critical('critical write log')
    