"""Данный вариант будет рабоать только у меня(ну может еще у кого запустится)"""


import os
import subprocess
import time

PROCESS = []

catalog = os.getcwd()
p = f'python "{catalog}/server.py"'
PROCESS.append(subprocess.Popen([
    'konsole',
    '-e',
    p])
)
print(p)
time.sleep(0.1)
for i in range(2):
    p = f'python "{catalog}/client.py" -n user_{i+1}'
    PROCESS.append(subprocess.Popen([
        'konsole',
        '-e',
        p])
    )
    print(p)
    time.sleep(0.5)
