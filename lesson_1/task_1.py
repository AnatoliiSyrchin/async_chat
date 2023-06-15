"""
Задание 1.

Каждое из слов «разработка», «сокет», «декоратор» представить
в буквенном формате и проверить тип и содержание соответствующих переменных.
Затем с помощью онлайн-конвертера преобразовать
в набор кодовых точек Unicode (НО НЕ В БАЙТЫ!!!)
и также проверить тип и содержимое переменных.

*Попытайтесь получить кодовые точки без онлайн-конвертера!
без хардкода!

Подсказки:
--- 'разработка' - буквенный формат
--- '\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430' - набор кодовых точек
--- используйте списки и циклы, не дублируйте функции
"""

list_of_words = ['разработка', 'сокет', 'декоратор']

def confert_to_code_points(text: str) -> str:
    code_points_bytes = text.encode('unicode-escape')
    code_points_str = code_points_bytes.decode('utf-8')
    return code_points_str

for word in list_of_words:
    type_of_variable = type(word)
    code_points = confert_to_code_points(word)
    type_of_code_points_variable = type(code_points)
    print(f'буквенный формат: {word}, тип переменной: {type_of_variable}\nнабор буквенных точек: {code_points}, тип переменной: {type_of_code_points_variable}')
    print('-' * 30)
