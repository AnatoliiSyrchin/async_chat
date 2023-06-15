"""
Задание 3.

Определить, какие из слов «attribute», «класс», «функция», «type»
невозможно записать в байтовом типе с помощью маркировки b'' (без encode decode).

Подсказки:
--- используйте списки и циклы, не дублируйте функции
--- обязательно!!! усложните задачу, "отловив" исключение,
придумайте как это сделать
"""


list_of_words = ['attribute', 'класс', 'функция', 'type']
for word in list_of_words:
    print(f'буквенный формат: {word}')
    try:
        word_in_byte_format = bytes(word, encoding='ascii')
        print(f'в байтовом формате: {word_in_byte_format}')
    except UnicodeEncodeError as err:
        print(err)
    print('-' * 30)
