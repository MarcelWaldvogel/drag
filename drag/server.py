#!/usr/bin/python3
#
# drag — Lightweight Webhook server for Docker containers
#
# Copyright (C) 2021 Marcel Waldvogel

import hashlib
import hmac
import logging
import os
import sys
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

VERSION = '0.1.0'

MAX_REQUEST_LEN = 100 * 1024

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)


class WebhookRequestHandler(BaseHTTPRequestHandler):
    def version_string(self):
        return "drag/" + VERSION

    def do_POST(self):
        # Based on https://github.com/pstauffer/gitlab-webhook-receiver
        logging.info("Hook received")

        body_length = int(self.headers['Content-Length'])
        json_payload = self.rfile.read(body_length)
        if (self.headers['X-Gitlab-Token'] != drag_secret
                and self.headers['X-Hub-Signature'] !=
                'sha1=' + hmac.new(bytes(drag_secret, 'UTF-8'), json_payload,
                                   hashlib.sha1).hexdigest()):
            self.send_response(403, 'Invalid token')
            logging.error("No or invalid GitLab token/GitHub signature")
            self.end_headers()
            return

        # We do not need to decode the JSON for now
        # json_params = {}
        # if len(json_payload) > 0:
        #    json_params = json.loads(json_payload.decode('utf-8'))

        try:
            subprocess.run(drag_command, check=True)
            logging.info("Ran hook")
            self.send_response(200, "OK")
        except subprocess.CalledProcessError:
            logging.error("Hook failed")
            self.send_response(500, "Command failed")
        finally:
            self.end_headers()


def webhook():
    httpd = HTTPServer(('', 1291), WebhookRequestHandler)
    logging.info("Start serving")
    httpd.serve_forever()


def main():
    global drag_secret, drag_command
    drag_secret = os.getenv('DRAG_SECRET')
    drag_command = os.getenv('DRAG_COMMAND')
    if drag_secret is None or drag_command is None:
        exit("Both DRAG_SECRET and DRAG_COMMAND environment variables needed")
    pid = os.fork()
    if pid == 0:
        # Process webhook requests in child process
        webhook()
    else:
        # Replace parent process with original service
        try:
            os.execvp(sys.argv[1], sys.argv[1:])
        except OSError as e:
            exit(f"Could not run {sys.argv}: {e}")


if __name__ == '__main__':
    main()
