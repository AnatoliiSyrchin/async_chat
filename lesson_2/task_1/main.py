"""
1.Задание на закрепление знаний по модулю CSV.
Написать скрипт, осуществляющий выборку определенных данных из файлов info_1.txt, info_2.txt, info_3.txt
и формирующий новый «отчетный» файл в формате CSV. Для этого:
Создать функцию get_data(), в которой в цикле осуществляется перебор файлов с данными, их открытие и считывание данных.
В этой функции из считанных данных необходимо с помощью регулярных выражений извлечь значения параметров
«Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
Значения каждого параметра поместить в соответствующий список. Должно получиться четыре списка — например, os_prod_list, os_name_list, os_code_list, os_type_list.
В этой же функции создать главный список для хранения данных отчета — например, main_data — и поместить в него названия столбцов отчета в виде списка: «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
Значения для этих столбцов также оформить в виде списка и поместить в файл main_data (также для каждого файла)
Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл.
В этой функции реализовать получение данных через вызов функции get_data(), а также сохранение подготовленных данных в соответствующий CSV-файл;
Проверить работу программы через вызов функции write_to_csv()
"""


import glob
import os
import re
import csv
 

def get_data(file_list: list) -> list:
    main_data = [['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы'],]
    os_prod_list = []
    os_name_list = []
    os_code_list = []
    os_type_list = []
    for file in files_list:
        with open(file) as f:
            text = f.read()
            os_prod_regex_pattern = re.compile(r'Изготовитель системы:\s*\S*')
            os_prod_result = os_prod_regex_pattern.findall(text)[0].split()[2]
            os_prod_list.append(os_prod_result)

            os_name_regex_pattern = re.compile(r'Название ОС:\s*Microsoft\s*(\S*\s\S*)')
            os_name_result = os_name_regex_pattern.findall(text)[0]
            os_name_list.append(os_name_result)

            os_code_regex_pattern = re.compile(r'Код продукта:\s*\S*')
            os_code_result = os_code_regex_pattern.findall(text)[0].split()[2]
            os_code_list.append(os_code_result)

            os_type_regex_pattern = re.compile(r'Тип системы:\s*\S*')
            os_type_result = os_type_regex_pattern.findall(text)[0].split()[2]
            os_type_list.append(os_type_result)

    main_data += zip(os_prod_list, os_name_list, os_code_list, os_type_list)
    return main_data

def write_csv(file_list: list, filename: str) -> None:
    data = get_data(file_list)

    with open(filename, 'w') as f:
        f_writer = csv.writer(f)
        f_writer.writerows(data)


if __name__ == '__main__':
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    files_list = glob.glob(cur_dir + '/*.txt')
    FILENAME = cur_dir + "/data_report.csv"

    write_csv(files_list, FILENAME)

    with open(FILENAME) as f:
        print(f.read())