""" Module with exceptions """


# Исключение - ошибка сервера
class ServerError(Exception):
    """ An exception class for server errors handling """

    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


# Ошибка - отсутствует обязательное поле в принятом словаре.
class ReqFieldMissingError(Exception):
    """
    An exception class is generated
    if there is no required field in the accepted dictionary.
    """

    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'В принятом словаре отсутствует обязательное поле' \
               f'{self.missing_field}.'
