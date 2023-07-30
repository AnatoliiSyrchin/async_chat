import subprocess
import sys


python = sys.executable

PROCESS = []

PROCESS.append(subprocess.Popen(f'{python} server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
for i in range(2):
    PROCESS.append(subprocess.Popen(f'{python} client.py -n user_{i + 1}',
                                    creationflags=subprocess.CREATE_NEW_CONSOLE))

