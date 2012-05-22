#!/usr/bin/env python

import datetime
import json
from optparse import OptionParser
import os.path
import re
import sys


B_RECORD_RE = re.compile(r'^B(\d{2})(\d{2})(\d{2})(\d{2})(\d{5})([NS])(\d{3})(\d{5})([EW])([AV])(\d{5})(\d{5})')
HFDTE_RECORD_RE = re.compile(r'^HFDTE(\d{2})(\d{2})(\d{2})')
HFPLT_RECORD_RE = re.compile(r'^HFPLT[^:]*:(.*)$')


def main(argv):
    option_parser = OptionParser()
    option_parser.add_option('-o', '--output', metavar='FILENAME')
    options, args = option_parser.parse_args(argv[1:])
    czml = []
    for arg in args:
        cartographicDegrees = []
        epoch = None
        id = os.path.basename(arg)
        date = None
        for line in open(arg):
            m = B_RECORD_RE.match(line)
            if m:
                time = datetime.time(*map(int, m.group(1, 2, 3)))
                dt = datetime.datetime.combine(date, time)
                if epoch is None:
                    epoch = dt
                latitude = int(m.group(4)) + int(m.group(5)) / 60000.0
                if m.group(6) == 'S':
                    latitude = -latitude
                longitude = int(m.group(7)) + int(m.group(8)) / 60000.0
                if m.group(9) == 'S':
                    longitude = -longitude
                height = int(m.group(11)) or int(m.group(12))
                cartographicDegrees.extend([(dt - epoch).seconds, longitude, latitude, height])
                continue
            m = HFDTE_RECORD_RE.match(line)
            if m:
                date = datetime.date(2000 + int(m.group(3)), int(m.group(2)), int(m.group(1)))
                continue
            m = HFPLT_RECORD_RE.match(line)
            if m:
                id = m.group(1).strip()
                continue
        czml.append({
            'id': id,
            'position': {
                'epoch': epoch.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'cartographicDegrees': cartographicDegrees,
            },
        })
    if options.output in (None, '-'):
        json.dump(czml, sys.stdout)
    else:
        with open(options.output, 'w') as fp:
            json.dump(czml, fp)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
