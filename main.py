import argparse
import datetime
import json
import os
import sys
import threading

import bottle


class Logger:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.lock = threading.Lock()

    def log(self, message):
        with self.lock:
            with open(os.path.join(self.data_dir, self._get_current_filename()), 'a') as f:
                f.write(message.strip('\n') + '\n')

    def _get_current_filename(self):
        return datetime.datetime.now(datetime.UTC).strftime('%Y%m%d') + '.json.log'

logger: Logger = None

@bottle.post('/pub')
def handle_publish():
    if not bottle.request.json:
        bottle.abort(400, 'empty body')

    body = bottle.request.json.copy()
    headers = {}
    for k, v in bottle.request.headers.items():
        if k.lower().startswith('x-limit-'):
            headers[k] = v
    body['_meta'] = {'headers': headers}

    body_str = json.dumps(body)
    if len(body_str) > 1024:
        raise ValueError(f"Body too large: {body_str}")
    logger.log(body_str)

    return '[]'

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--host', default='localhost')
parser.add_argument('-p', '--port', type=int, default=8035)
parser.add_argument('-d', '--data-dir', default='data')
parser.add_argument('--use-gunicorn', action='store_true')
args = parser.parse_args()

os.makedirs(args.data_dir, exist_ok=True)
logger = Logger(args.data_dir)

if args.use_gunicorn:
    sys.argv = sys.argv[:1]
    bottle.run(host=args.host, port=args.port, server='gunicorn')
else:
    bottle.run(host=args.host, port=args.port)
