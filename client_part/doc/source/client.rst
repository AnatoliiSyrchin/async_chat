Client module documentation
===========================

Clients part of chat application

could be called with command
    ``python client.py {server_ip_address} {port} -n(--name) {users_name} -p {password}``

if no arguments passed - will be used default parameters for server ip address and port,
clients name and password has to be entered in start dialog

client.py
---------

starting module with argument parser

**get_client_parameters() -> tuple:**
    Getting parameters from command line

transport.py
------------

.. automodule:: client.transport
	:members:

add_contact.py
--------------

.. automodule:: client.add_contact
	:members:

del_contact.py
--------------

.. automodule:: client.del_contact
	:members:

main_window.py
--------------

.. automodule:: client.main_window
	:members:

main_window_conv.py
-------------------

.. automodule:: client.main_window_conv
	:members:

start_dialog.py
---------------

.. automodule:: client.start_dialog
	:members: