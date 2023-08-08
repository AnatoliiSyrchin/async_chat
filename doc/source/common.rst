Common package
=================

Package with modules used both by clients and server.

module decorators.py
--------------------

.. automodule:: common.decorators
	:members:

module descriptors.py
---------------------

.. autoclass:: common.descriptors.Port
    :members:

module errors.py
--------------------

.. automodule:: common.errors
	:members:

module metaclasses.py
---------------------

* class ServerMaker - metaclass checking, that there are no clients methods in class, and that server socket is TCP and uses IPc4 protocol


* class ClintMaker - metaclass checking, that there are no server methods in class, and that the socket is not created inside the class constructor

module utils.py
--------------------

.. automodule:: common.utils
	:members:

module variables.py
--------------------

global projects variables