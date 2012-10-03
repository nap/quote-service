__author__ = 'Jean-Bernard Ratte - jean.bernard.ratte@unary.ca'

import codecs
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

_bad_request = "HTTP/1.1 400 Bad Request\r\n" \
               "Server: quote-service/0.1.1\r\n\r\n"

_ok_request = "HTTP/1.1 200 Connection established\r\n" \
              "Connection: keep-alive\r\nContent-Length: %s bytes\r\n" \
              "Content-Type: application/json; charset=utf-8\r\n" \
              "Server: quote-service/0.1.1\r\n\r\n%s\r\n\r\n"


def get_socket(host, port, max_connections):
    sock = socket.socket(socket.AF_INET)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(0)
    sock.bind((host, int(port)))
    sock.listen(int(max_connections))
    return sock

def connection_ready(sok, fd, events):
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
    if message[:14] == 'GET / HTTP/1.1':
        quote = json.dumps(quotes[randint(1, len(quotes))])
        client.write(_ok_request % (len(quote), quote), callback=client.close)

    else:
        client.write(_bad_request, callback=client.close)


quotes = ''
if __name__ == '__main__':
    if '-h' in sys.argv:
        print 'Usage: python quote_service.py [quote_file] [port] [max_connections]'
        print 'Default: python quote_service.py %s %s %s' % (INPUT, DEFAULT_PORT, MAXIMUM_CONNEXIONS)
        print 'Valid JSON (ex: filename.json) format: [{"key","value"}]'

    else:
        if len(sys.argv) > 1:
            try:
                with open(sys.argv[1]) as json_file: pass
                DEFAULT_PORT = int(sys.argv[2])
                MAXIMUM_CONNEXIONS = int(sys.argv[3])

            except IOError:
                raise IOError('Invalid JSON file.')

            except ValueError:
                raise ValueError('Invalid Port number or Maximum Connection number error.')

        with codecs.open(INPUT, 'r', 'utf-8') as json_file:
            quotes = json.loads(''.join(json_file.readlines()))
            io_loop = ioloop.IOLoop.instance()

            sok = get_socket(DEFAULT_HOST, DEFAULT_PORT, MAXIMUM_CONNEXIONS)

            callback = functools.partial(connection_ready, sok)
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

            except (IOError, ValueError) as e:
                print e.message