__author__ = 'Jean-Bernard Ratte - jean.bernard.ratte@unary.ca'

import json
import functools
import socket
import fcntl
import errno
import sys
from os import O_NONBLOCK
from tornado import ioloop, iostream, stack_context
from random import randint

INPUT = 'quote.json'
DEFAULT_PORT = 8080
DEFAULT_HOST = ''
MAXIMUM_CONNEXIONS = 5000
JSONP_FUNC_NAME = ''

# Response to all HTTP request with 501 status code except get GET 
_bad_request = "HTTP/1.1 501 Not Implemented\r\n" \
               "Server: quote-service/0.1.1\r\n\r\n"

# Response to all GET request with a 200 OK status code
_ok_request = "HTTP/1.1 200 Connection established\r\n" \
              "Connection: keep-alive\r\n" \
              "Content-Length: %s\r\n" \
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


def connection_ready(sok, fd, events):
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
    callback = stack_context.wrap(functools.partial(send_quote, client))
    client.read_until("\r\n\r\n", callback)


def send_quote(client, message):
    """
    Verify that the client sent a GET message then send a random quote
    to finally close the connection when the quote is fully sent.
    """
    if message[:14] == 'GET / HTTP/1.1':
        quote = json.dumps(quotes[randint(1, len(quotes))])
        if len(JSONP_FUNC_NAME) > 0:
            quote = "%s(%s);" % (JSONP_FUNC_NAME, quote)

        client.write(_ok_request % (len(quote), quote), callback=client.close)

    else:
        client.write(_bad_request, callback=client.close)


if __name__ == '__main__':
    if '-h' in sys.argv:
        print 'Usage: python quote_service.py [quote_file] [port] [max_connections] [PADDING]'
        print 'Default: python quote_service.py %s %s %s' % (INPUT, DEFAULT_PORT, MAXIMUM_CONNEXIONS)
        print 'Valid JSON (ex: filename.json) format: [{"key","value"}]'

    else:
        if len(sys.argv) > 1:
            try:
                with open(sys.argv[1]) as f: f.close()
                INPUT = sys.argv[1]
                DEFAULT_PORT = int(sys.argv[2])
                MAXIMUM_CONNEXIONS = int(sys.argv[3])
                JSONP_FUNC_NAME = str(sys.argv[4]).replace(' ', '').strip()

            except IOError:
                raise IOError('Invalid JSON file.')

            except ValueError:
                raise ValueError('Invalid Port number or Maximum Connection number error.')

        with open(INPUT, 'r') as json_file:
            # Load all the quotes in memory
            quotes = json.loads(''.join(json_file.readlines()))
            json_file.close()

            sok = get_socket(DEFAULT_HOST, DEFAULT_PORT, MAXIMUM_CONNEXIONS)
            callback = functools.partial(connection_ready, sok)

            io_loop = ioloop.IOLoop.instance()
            # Get socket and wait for connections
            io_loop.add_handler(sok.fileno(), callback, io_loop.READ)

            # Launch the io loop.
            try:
                print "Starting ... "
                print "Serving %s quotes on port %s." % (len(quotes), DEFAULT_PORT)
                print "Press Ctrl + C to quit. "
                io_loop.start()

            except KeyboardInterrupt:
                io_loop.stop()
                print "\r\n/!\ Quote service exited cleanly."
