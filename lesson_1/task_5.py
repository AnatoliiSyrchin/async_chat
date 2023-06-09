"""
Задание 5.

Выполнить пинг веб-ресурсов yandex.ru, youtube.com и
преобразовать результаты из байтовового в строковый тип на кириллице.

Подсказки:
--- используйте модуль chardet, иначе задание не засчитается!!!
"""

import subprocess
import chardet

addresses = ['yandex.ru', 'youtube.com']

for adress in addresses:
    args = ['ping', adress]
    ping_process = subprocess.Popen(args, stdout=subprocess.PIPE)
    for line in ping_process.stdout:
        result = chardet.detect(line)
        print(line.decode(encoding=result['encoding']))
    print('#' * 60)
 