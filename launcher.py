import subprocess
import sys


PYTHON = sys.executable

PROCESS = []

PROCESS.append(subprocess.Popen(f'{PYTHON} server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
for i in range(2):
    PROCESS.append(subprocess.Popen(f'{PYTHON} client.py -n user_{i + 1}',
                                    creationflags=subprocess.CREATE_NEW_CONSOLE))

