"""
2. Задание на закрепление знаний по модулю json.
  Есть файл orders в формате JSON с информацией о заказах.
  Написать скрипт, автоматизирующий его заполнение данными.
Для этого:
a. Создать функцию write_order_to_json(), в которую передается 5 параметров —
  товар (item), количество (quantity), цена (price), покупатель (buyer), дата (date).
  Функция должна предусматривать запись данных в виде словаря в файл orders.json.
  При записи данных указать величину отступа в 4 пробельных символа;
b. Проверить работу программы через вызов функции write_order_to_json() с передачей
  в нее значений каждого параметра.

"""
import json
import os


def write_order_to_json(file: str, item: str, quantity: str, price: str, buyer: str, date: str):
    data = {
        'item': item,
        'quantity': quantity,
        'price': price,
        'buyer': buyer,
        'date': date
    }

    with open(file) as f:
        obj = json.load(f)

    obj['orders'].append(data)

    with open(file, 'w') as f:
        json.dump(obj, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    filename = cur_dir + "/orders.json"
    test_data = [
        ['компьютер', 1, 1000, 'buyer', '01.01.23'],
        ['принтер', 2, 300, 'buyer', '02.02.22'],
    ]
    for list in test_data:
        write_order_to_json(filename, list[0], list[1], list[2], list[3], list[4])
    with open(filename) as f:
        test_obj = json.load(f)
        print(test_obj)
