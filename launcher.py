import subprocess

PROCESS = []

while True:

    ANSWER = input('Выбирите действие: q - выход, s - запустить сервер и клиенты, x - закрыть все окна: ')
    
    if ANSWER == 'q':
        break
    elif ANSWER == 's':
        PROCESS.append(subprocess.Popen('python server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
        for i in range(5):
            PROCESS.append(subprocess.Popen('python client.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
    elif ANSWER == 'x':
        while PROCESS:
            VICTIM = PROCESS.pop()
            VICTIM.kill()