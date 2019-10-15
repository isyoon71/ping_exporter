#!/usr/bin/env python
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import threading
import sys
import subprocess
from urlparse import parse_qs, urlparse
import logging
import os

def locate(file):
    #Find the path for fping
    for path in os.environ["PATH"].split(os.pathsep):
        if os.path.exists(os.path.join(path, file)):
                return os.path.join(path, file)
    return "{}".format(file)

def ping(host, interval):
    output = []

    ping_command = 'ping {} -q -c 1 -W {}'.format(host, interval)
    logger.info(ping_command)
    cmd_output = subprocess.Popen(ping_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
    regx = '100.0%'
    if regx in cmd_output[0]:
        return 0
    else:
        return 1

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

class GetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        #Parse the url
        parsed_path = urlparse(self.path).query
        value = parse_qs(parsed_path)

        #Retrieve the ping target
        if "target" in value:
            address = value['target'][0]
        else:
            address = "8.8.8.8"

        #Retrieve ping count
        if "count" in value:
            count = value['count'][0]
        else:
            count = 5

        #Retrieve ping interval
        if "interval" in value and int(value['interval'][0]) > 1:
            interval = value['interval'][0]
        else:
            interval = 8

        successValue = 0
        usingCount = 0
        requestCount = count
        count = int(count)

        while count > 0:
            returnValue = ping(address, interval)
            count = count - 1
            usingCount = usingCount + 1
            if returnValue == 1:
                successValue = 1
                break

        output = []
        output.append("ping_success {}".format(successValue))
        output.append("ping_request_count {}".format(requestCount))
        output.append("ping_use_count {}".format(usingCount))
        output.append('')

        message = '\n'.join(output)

        #Prepare HTTP status code
        self.send_response(200)
        self.end_headers()
        self.wfile.write(message)
        return

if __name__ == '__main__':
    #Locate the path of fping
    global filepath
    filepath = locate("ping")
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    #Check if there is a special port configured
    if len(sys.argv) >= 3:
        port = int(sys.argv[2])
    else:
        port = 8085
    logger.info('Starting server port {}, use <Ctrl-C> to stop'.format(port))
    server = ThreadedHTTPServer(('0.0.0.0', port), GetHandler)
    server.serve_forever()
