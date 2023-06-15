"""
3. Задание на закрепление знаний по модулю yaml.
Написать скрипт, автоматизирующий сохранение данных в файле YAML-формата. Для этого:
Подготовить данные для записи в виде словаря,
в котором первому ключу соответствует список, второму — целое число, третьему — вложенный словарь,
где значение каждого ключа — это целое число с юникод-символом, отсутствующим в кодировке ASCII (например, €);
Реализовать сохранение данных в файл формата YAML — например, в файл file.yaml.
При этом обеспечить стилизацию файла с помощью параметра default_flow_style,
а также установить возможность работы с юникодом: allow_unicode = True;
Реализовать считывание данных из созданного файла и проверить, совпадают ли они с исходными.
"""
import yaml
import os

test_data = {
    'items': ['computer', 'printer', 'keyboard', 'mouse'],
    'items_prices': {
        'computer': '10000\u20BD-100000\u20BD',
        'printer': '5000\u20BD-50000\u20BD',
        'keyboard': '500\u20BD-5000\u20BD',
        'mouse': '500\u20BD-5000\u20BD'
    },
    'items_quantity': 4
}

cur_dir = os.path.dirname(os.path.abspath(__file__))
filename = cur_dir + "/file.yaml"

with open(filename, 'w', encoding='utf-8') as f_n:
    yaml.dump(test_data, f_n, default_flow_style=False, allow_unicode=True)

with open(filename, encoding='utf-8') as f_n:
    print(f_n.read())

