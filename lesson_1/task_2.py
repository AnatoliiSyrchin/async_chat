"""
Задание 2.

Каждое из слов «class», «function», «method» записать в байтовом формате
без преобразования в последовательность кодов
не используя!!! методы encode и decode)
и определить тип, содержимое и длину соответствующих переменных.

Подсказки:
--- b'class' - используйте маркировку b''
--- используйте списки и циклы, не дублируйте функции
"""

list_of_words = [b'class', b'function', b'method']
for word in list_of_words:
    type_of_variable = type(word)
    print(f'тип переменной: {type_of_variable}')
    print(f'буквенный формат: {word}')
    length_of_variable = len(word)
    print(f'длина: {length_of_variable}')
    print('-' * 30)
