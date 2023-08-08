Client module documentation
===========================

Server part of chat application
Handling messages from clients.

could be called with command
    ``python server.py -a(--address) -p(--port)``

if no arguments passed - will be used default parameters for ip address and port

server.py
---------

starting module with argument parser

**get_server_parameters(port, address) -> tuple:**
    Getting parameters from command line

**server_config**
    Getting parameters from config file

**save_server_config**
    Saving server parameters to config file

**refresh_tab**
    It shouldn't be here, I`ll move it later. may be

server_gui.py
-------------

server interface

server_transport.py
-------------------

module with main server class
