#!/usr/bin/python
#
#   Copyright 2017 Gabriel Cebrian
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import argparse
import hmtools.bd
import sys

def parse_arguments(argv):
    """Parses the command line arguments and checks that they meet the
    requirements to perform the operations of the program. Returns two arrays of
    points (tuples) in the form (bitrate, psnr), and a boolean stating whether
    to use piecewiese or cubic interpolation.

    Keyword arguments:
    argv -- Command line arguments.
    """
    argument_parser = argparse.ArgumentParser(description='Calculates the '
            'BD-rate between two rate-distortion curves.')

    argument_parser.add_argument('-o', '--old', action='store_true',
            default=False, required=False, help='use the old cubic polynomial '
            'interpolation function to calculate the BD-rate, instead of the '
            'piecewise cubic interpolation function.', dest='use_old_bdrate')
    argument_parser.add_argument('-b', '--base', nargs='+', type=float,
            required=True, help='set of rate-distortion values of the baseline '
            'encoder.', metavar='bitrate psnr', dest='base')
    argument_parser.add_argument('-t', '--test', nargs='+', type=float,
            required=True, help='set of rate-distortion values of the encoder '
            'being tested.', metavar='bitrate psnr', dest='test')

    arguments = argument_parser.parse_args(argv)

    if (len(arguments.base) % 2) != 0:
        argument_parser.error('incorrect baseline parameters. Please check you '
                'have introduced the (bitrate psnr) tuples correctly.')
    if (len(arguments.test) % 2) != 0:
        argument_parser.error('incorrect test parameters. Please check you '
                'have introduced the (bitrate psnr) tuples correctly.')
    if len(arguments.base) < 8:
        argument_parser.error('you must provide at least 4 points for the '
                'baseline encoder.')
    if len(arguments.test) < 8:
        argument_parser.error('you must provide at least 4 points for the '
                'encoder being tested.')

    base = zip(arguments.base[0::2], arguments.base[1::2])
    test = zip(arguments.test[0::2], arguments.test[1::2])
    use_old_bdrate = arguments.use_old_bdrate

    return base, test, use_old_bdrate

def main(argv):
    base, test, use_old_bdrate = parse_arguments(argv[1:])
    base = sorted(set(base))
    test = sorted(set(test))

    if use_old_bdrate:
        bdrate = hmtools.bd.bdrate_old(base, test)
    else:
        bdrate = hmtools.bd.bdrate(base, test)

    print('{:0.4f}'.format(bdrate))

if __name__ == "__main__":
    main(sys.argv)
