#!/usr/bin/env python

from cStringIO import StringIO
import datetime
import json
from optparse import OptionParser
import os.path
import re
import sys
from zipfile import ZipFile


B_RECORD_RE = re.compile(r'^B(\d{2})(\d{2})(\d{2})(\d{2})(\d{5})([NS])(\d{3})(\d{5})([EW])([AV])(\d{5})(\d{5})')
HFDTE_RECORD_RE = re.compile(r'^HFDTE(\d{2})(\d{2})(\d{2})')
HFPLT_RECORD_RE = re.compile(r'^HFPLT[^:]*:(.*)$')


def igc2czml(id, f, geometry=None):
    cartographicDegrees = []
    epoch = None
    date = None
    for line in f:
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
    result = {
        'id': id,
        'availability': '%s/%s' % (epoch.strftime('%Y-%m-%dT%H:%M:%SZ'), dt.strftime('%Y-%m-%dT%H:%M:%SZ')),
        'position': {
            'epoch': epoch.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'cartographicDegrees': cartographicDegrees,
        },
    }
    if geometry:
        result.update(geometry)
    return result


def zip2czml(arg, geometry=None):
    result = []
    with ZipFile(arg) as zipfile:
        for zipinfo in zipfile.infolist():
            result.append(igc2czml(zipinfo.filename, zipfile.open(zipinfo), geometry))
    return result


def main(argv):
    option_parser = OptionParser()
    option_parser.add_option('-g', '--geometry')
    option_parser.add_option('-i', '--indent', type=int)
    option_parser.add_option('-o', '--output', metavar='FILENAME')
    option_parser.add_option('-s', '--sort-keys', action='store_true')
    options, args = option_parser.parse_args(argv[1:])
    if options.geometry:
        geometry = json.load(options.geometry)
    else:
        geometry = {
            'point': {
                'color': {
                    'rgba': [255, 0, 0, 255]
                },
                'pixelSize': 8,
            }
        }
    czml = []
    for arg in args:
        if arg.lower().endswith('.igc'):
            czml.append(igc2czml(os.path.basename(arg), open(arg), geometry=geometry))
        elif arg.lower().endswith('.zip'):
            czml.extend(zip2czml(open(arg)))
        else:
            assert RuntimeError  # FIXME

    if options.output in (None, '-'):
        json.dump(czml, sys.stdout, indent=options.indent, sort_keys=options.sort_keys)
    else:
        with open(options.output, 'w') as fp:
            json.dump(czml, fp, indent=options.indent, sort_keys=options.sort_keys)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
