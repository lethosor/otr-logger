import argparse
import datetime
import json
import os
import re
import tarfile

import requests

class DataRecord:
    payload: dict
    meta: dict  # optional

    def __init__(self, payload, meta=None):
        if 'created_at' not in payload:
            raise ValueError('missing key: created_at')
        self.payload = payload
        self.meta = meta

    def __repr__(self):
        return f'{type(self).__name__}(payload={self.payload!r}, meta={self.meta!r})'

    @property
    def __key(self):
        return (self.payload['created_at'], self.payload.get('lat'), self.payload.get('lon'))

    def __hash__(self):
        return hash(self.__key)

    def __eq__(self, other):
        return self.__key == other.__key

    def __lt__(self, other):
        return self.payload['created_at'] < other.payload['created_at']

    @property
    def description(self):
        time_str = datetime.datetime.fromtimestamp(self.payload['created_at'], tz=datetime.UTC).astimezone(None).strftime('%c %Z')
        return f'{time_str} ({self.payload["lat"]}, {self.payload["lon"]})'

def parse_records(file, filename, preprocess_line=None):
    for line_i, line in enumerate(file.readlines()):
        try:
            if preprocess_line:
                line = preprocess_line(line)
            cur_obj = json.loads(line)
        except json.JSONDecodeError as e:
            print(f'invalid json: {filename}:{line_i + 1}: {e}')
            continue
        if not isinstance(cur_obj, dict):
            continue
        if cur_obj.get('_type') != 'location':
            continue
        meta = None
        if '_meta' in cur_obj:
            meta = cur_obj.pop('_meta')
        yield DataRecord(payload=cur_obj, meta=meta)

def post_record(args, record: DataRecord):
    if args.dry_run:
        print('would write:', record.description)
        return

    print('writing:', record.description)
    requests.post(args.endpoint, headers={'X-Limit-U': args.user, 'X-Limit-D': args.device}, json=record.payload)

def find_data_files(data_folder):
    for root, dirnames, filenames in os.walk(data_folder):
        for filename in filenames:
            if re.match(r'\d{4}-\d{2}\.rec', filename):
                yield os.path.join(root, filename)

parser = argparse.ArgumentParser()
parser.add_argument('archive')
parser.add_argument('-u', '--user', required=True)
parser.add_argument('-d', '--device', required=True)
parser.add_argument('-e', '--endpoint', required=True)
parser.add_argument('-f', '--data-folder', required=True)
parser.add_argument('-n', '--dry-run', action='store_true')
parser.add_argument('-l', '--limit', type=int)

def main(args):
    records_in_archive = []
    with tarfile.open(args.archive) as archive:
        for member in archive.getmembers():
            f = archive.extractfile(member)
            if f is None:
                continue
            with f:
                records_in_archive.extend(parse_records(f, member.name))
    records_in_archive.sort()
    print('records in archive:', len(records_in_archive))

    records_in_data = []
    for data_filename in find_data_files(args.data_folder):
        with open(data_filename) as f:
            records_in_data.extend(parse_records(f, data_filename, preprocess_line=lambda line: line[line.find('{'):]))
    records_in_data.sort()
    print('records in data folder:', len(records_in_data))

    records_to_add = [r for r in records_in_archive if r not in records_in_data]
    print('records to add:', len(records_to_add))

    for i, r in enumerate(records_to_add):
        if args.limit and i >= args.limit:
            break
        post_record(args, r)

if __name__ == '__main__':
    main(args=parser.parse_args())
