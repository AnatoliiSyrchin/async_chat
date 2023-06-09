"""
Задание 6.
Создать текстовый файл test_file.txt, заполнить его тремя строками:
«сетевое программирование», «сокет», «декоратор».
Проверить кодировку файла по умолчанию.
Принудительно открыть файл в формате Unicode и вывести его содержимое.
"""

import chardet

list_of_lines = ['сетевое программирование\n', 'сокет\n', 'декоратор\n']

with open('lesson_1/text.txt', 'w') as f:
    f.writelines(list_of_lines)

with open('lesson_1/text.txt', 'rb') as f:
    content_b = f.read()

encoding = chardet.detect(content_b)['encoding']

with open('lesson_1/text.txt', 'r', encoding=encoding) as f:
    print(f.read())