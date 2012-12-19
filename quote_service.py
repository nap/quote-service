__author__ = 'Jean-Bernard Ratte - jean.bernard.ratte@unary.ca'

import json
import functools
import socket
import fcntl
import errno
import argparse
from os import O_NONBLOCK
from tornado import ioloop, iostream, stack_context
from random import randint

END_POINT = "/"
GET_MSG = 'GET %s HTTP/1.1' % END_POINT
INPUT = 'quote.json'
DEFAULT_PORT = 8080
DEFAULT_HOST = ''
MAXIMUM_CONNEXIONS = 5000

# Response to all HTTP request with 501 status code except get GET 
_bad_request = "HTTP/1.1 405 Method Not Allowed\r\n" \
               "Connection: close\r\n" \
               "Allow: GET\r\n" \
               "Server: quote-service/0.1.1\r\n\r\n"

# Response to all GET request with a 200 OK status code
_ok_request = "HTTP/1.1 200 OK\r\n" \
              "Connection: close\r\n" \
              "Content-Length: %s\r\n" \
              "Content-Language: fr\r\n" \
              "Content-Type: application/json; charset=utf-8\r\n" \
              "Server: quote-service/0.1.1\r\n\r\n%s\r\n\r\n"


def get_socket(host, port, max_connections):
    """
    Create a listening socket to accept client connections and set it as non-blocking.
    """
    sock = socket.socket(socket.AF_INET)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(0)
    sock.bind((host, int(port)))
    sock.listen(int(max_connections))
    return sock


def connection_ready(sok, fd, events, padding=None):
    """
    On a read event, we accept the connection and wrap it in a IOStream 
    and make sure that the socket is non-blocking.
    """
    # Set the file descriptor of the current socket as non-blocking to avoid EAGAIN error.
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~O_NONBLOCK)

    try:
        # Accept connection from client and set it as nonblocking
        connection, address = sok.accept()
        connection.setblocking(0)

    except socket.error, e:
        if e[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
            raise

        return

    # Wrap client socket into an IOStream
    client = iostream.IOStream(connection)
    callback = stack_context.wrap(functools.partial(send_quote, client, padding=padding))
    client.read_until("\r\n\r\n", callback)


def send_quote(client, message, padding=None):
    """
    Verify that the client sent a GET message then send a random quote
    to finally close the connection when the quote is fully sent.
    """
    if message[:len(GET_MSG)] == GET_MSG:
        quote = json.dumps(quotes[randint(0, len(quotes) - 1)])
        if padding:
            quote = "%s(%s);" % (padding, quote)

        if not client.closed():
            client.write(_ok_request % (len(quote), quote), callback=client.close)

    else:
        if not client.closed():
            client.write(_bad_request, callback=client.close)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    file_arg = {
        'dest': 'quote_file',
        'type': argparse.FileType('r'),
        'required': True,
        'help': 'format: [{"key": "value"}, {"key": "value"}]'
    }
    parser.add_argument('-f', **file_arg)

    port_arg = {
        'dest': 'port',
        'type': int,
        'default': DEFAULT_PORT,
        'required': False,
        'help': 'port number to accept connection to (Default: %s)' % DEFAULT_PORT
    }
    parser.add_argument('-p', **port_arg)

    max_arg = {
        'dest': 'max_connections',
        'type': int,
        'default': MAXIMUM_CONNEXIONS,
        'required': False,
        'help': 'number of maximum connection allowed (Default: %s)' % MAXIMUM_CONNEXIONS
    }
    parser.add_argument('-m', **max_arg)

    padding_arg = {
        'dest': 'padding',
        'type': str,
        'required': False,
        'help': 'JSONP function name'
    }
    parser.add_argument('--padding', **padding_arg)

    args = parser.parse_args()
    with args.quote_file as json_file:
        # Load all the quotes in memory
        quotes = json.loads(''.join(json_file.readlines()))

        sok = get_socket(DEFAULT_HOST, args.port, args.max_connections)
        callback = functools.partial(connection_ready, sok, padding=args.padding)

        io_loop = ioloop.IOLoop.instance()
        # Get socket and wait for connections
        io_loop.add_handler(sok.fileno(), callback, io_loop.READ)

        try: # Launch the io loop.
            print "Serving %s quotes on port %s." % (len(quotes), args.port)
            print "Press Ctrl + C to quit. "
            io_loop.start()

        except KeyboardInterrupt:
            io_loop.stop()
            print " bye!"