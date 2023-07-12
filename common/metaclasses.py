import dis
from socket import socket


class ServerVerifier(type):
    def __init__(cls, clsname, bases, clsdict):
        attrs = []
        for value in clsdict.values():
            try:
                func = dis.get_instructions(value)
                for instruction in func:
                    if instruction.opname == 'LOAD_METHOD' and instruction.argval == 'connect':
                        raise TypeError('В сервере не должно быть метода "connect"')
                    if instruction.opname == 'LOAD_ATTR' and instruction.argval in ('SOCK_STREAM', 'AF_INET'):
                        attrs.append(instruction.argval)
            except TypeError as err:
                pass
        if 'SOCK_STREAM' not in attrs or 'AF_INET' not in attrs:
            raise TypeError('Надо использовать сокетоы для работы по TCP')
        super().__init__(clsname, bases, clsdict)


class ClientVerifier(type):
    def __init__(cls, clsname, bases, clsdict):
        attrs = []
        for value in clsdict.values():
            try:
                func = dis.get_instructions(value)
                for instruction in func:
                    if instruction.opname == 'LOAD_METHOD' and instruction.argval in ('listen', 'accept'):
                        raise TypeError('В клиенте не должно быть методов "listen" и "accept"')
                    if instruction.opname == 'LOAD_ATTR' and instruction.argval in ('SOCK_STREAM', 'AF_INET'):
                        attrs.append(instruction.argval)
            except TypeError as err:
                if type(value) == socket:
                    raise TypeError('Нельзя создавать сокеты на уровне классов')
        if 'SOCK_STREAM' not in attrs or 'AF_INET' not in attrs:
            raise TypeError('Надо использовать сокетоы для работы по TCP')
        super().__init__(clsname, bases, clsdict)
