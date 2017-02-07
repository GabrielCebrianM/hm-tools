#!/usr/bin/python
#
#   Copyright 2017 Gabriel Cebrián
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
import collections
import hmtools.bd
import hmtools.parser
import os.path
import scipy.stats.mstats
import sys

def parse_arguments(argv):
    argument_parser = argparse.ArgumentParser(description='Parses the result '
            'files of two directories and provides the per-sequence results '
            'in terms of coding efficiency (BD-rate) and encoding time '
            '(speed-up and time reduction).')

    argument_parser.add_argument('-o', '--old', action='store_true',
            default=False, required=False, help='use the old cubic polynomial '
            'interpolation function to calculate the BD-rate, instead of the '
            'piecewise cubic interpolation function.', dest='use_old_bdrate')
    argument_parser.add_argument('-s', '--scale', nargs=1, type=int,
            default=4, required=False, help='number of digits shown to the '
            'right of the decimal point.', dest='scale')
    argument_parser.add_argument('-b', '--base', nargs=1, type=str,
            required=True, help='path of the directory containing the results '
            'of the baseline encoding.', dest='base_path')
    argument_parser.add_argument('-bp', '--base_pattern', nargs=1, type=str,
            required=True, help='pattern matching the filenames of the results '
            'of the baseline encoding. It must be a valid Python regular '
            'expression.', dest='base_pattern')
    argument_parser.add_argument('-t', '--test', nargs=1, type=str,
            required=True, help='path of the directory containing the results '
            'of the encoding tested.', dest='test_path')
    argument_parser.add_argument('-tp', '--test_pattern', nargs=1, type=str,
            required=True, help='pattern matching the filenames of the results '
            'of the encoding being tested. It must be a valid Python regular '
            'expression.', dest='test_pattern')

    arguments = argument_parser.parse_args(argv)

    #TODO: expanduser
    #TODO: check why sometimes arguments are lists, and others integers

    if not os.path.isdir(arguments.base_path[0]):
        argument_parser.error('path of the baseline encoding is not a '
            'directory')
    if not os.path.isdir(arguments.test_path[0]):
        argument_parser.error('path of the encoding being tested is not a '
            'directory')
    if arguments.scale[0] < 0:
        argument_parser.error('scale must be a positive value.')

    return arguments

def sort_sequences(sequences):
    test_sequences = collections.OrderedDict()
    test_sequences['Class A'] = ['Traffic', 'PeopleOnStreet', 'Nebuta', 'SteamLocomotive']
    test_sequences['Class B'] = ['Kimono', 'ParkScene', 'Cactus', 'BasketballDrive', 'BQTerrace']
    test_sequences['Class C'] = ['BasketballDrill', 'BQMall', 'PartyScene', 'RaceHorsesC']
    test_sequences['Class D'] = ['BasketballPass', 'BQSquare', 'BlowingBubbles', 'RaceHorses']
    test_sequences['Class E'] = ['FourPeople', 'Johnny', 'KristenAndSara']
    test_sequences['Class F'] = ['BasketballDrillText', 'ChinaSpeed', 'SlideEditing', 'SlideShow']

    sorted_sequences = collections.OrderedDict()
    sorted_sequences_list = []

    for category, category_sequences in test_sequences.items():
        for sequence in category_sequences:
            if sequence in sequences:
                if category not in sorted_sequences:
                    sorted_sequences[category] = []
                sorted_sequences[category].append(sequence)
                sorted_sequences_list.append(sequence)

    uncategorized_sequences = [sequence for sequence in sequences if sequence not in sorted_sequences_list]
    if uncategorized_sequences:
        sorted_sequences['Uncategorized'] = uncategorized_sequences

    return sorted_sequences

def calculate_results(sequences, base_results, test_results, use_old_bdrate):
    results = dict()

    all_bdrates = list()
    all_speedups = list()
    all_time_reductions = list()

    for category, category_sequences in sequences.items():
        for sequence in category_sequences:
            base_rd = set()
            test_rd = set()
            speedups = list()
            time_reductions = list()

            for sequence_id in base_results[sequence].keys():
                if 'rd' in base_results[sequence][sequence_id]:
                    base_rd.add((base_results[sequence][sequence_id]['rd']['a']['bitrate'], base_results[sequence][sequence_id]['rd']['a']['yuv_psnr']))

            for sequence_id in test_results[sequence].keys():
                if 'rd' in test_results[sequence][sequence_id]:
                    test_rd.add((test_results[sequence][sequence_id]['rd']['a']['bitrate'], test_results[sequence][sequence_id]['rd']['a']['yuv_psnr']))

            sequence_ids = set(base_results[sequence].keys() & test_results[sequence].keys())
            for sequence_id in sequence_ids:
                if 'perf' in base_results[sequence][sequence_id] and 'time' in base_results[sequence][sequence_id]['perf'] \
                        and 'perf' in test_results[sequence][sequence_id] and 'time' in test_results[sequence][sequence_id]['perf']:
                    base_time = base_results[sequence][sequence_id]['perf']['time']
                    test_time = test_results[sequence][sequence_id]['perf']['time']

                    speedups.append(base_time / test_time)
                    time_reductions.append((base_time - test_time) / base_time)

            results[sequence] = dict()
            results[sequence]['bdrate'] = float('nan')
            results[sequence]['speedup'] = float('nan')
            results[sequence]['time_reduction'] = float('nan')

            if len(base_rd) >= 4 and len(test_rd) >= 4:
                base_rd = sorted(base_rd)
                test_rd = sorted(test_rd)
                if use_old_bdrate:
                    bdrate = hevctools.bd.bdrate_old(base_rd, test_rd)
                else:
                    bdrate = hevctools.bd.bdrate(base_rd, test_rd)

                results[sequence]['bdrate'] = bdrate
                all_bdrates.append(bdrate)
            if len(speedups) > 0:
                speedup = sum(speedups) / len(speedups) #scipy.stats.mstats.gmean(speedups)

                results[sequence]['speedup'] = speedup
                all_speedups.append(speedup)
            if len(time_reductions) > 0:
                time_reduction = sum(time_reductions) / len(time_reductions)

                results[sequence]['time_reduction'] = time_reduction
                all_time_reductions.append(time_reduction)

    average = dict()
    average['bdrate'] = float('nan')
    average['speedup'] = float('nan')
    average['time_reduction'] = float('nan')

    if len(all_bdrates) > 0:
        average['bdrate'] = sum(all_bdrates) / len(all_bdrates)
    if len(all_speedups) > 0:
        average['speedup'] = sum(all_speedups) / len(all_speedups)
    if len(all_time_reductions) > 0:
        average['time_reduction'] = sum(all_time_reductions) / len(all_time_reductions)

    return results, average

def print_results(sequences, results, average, scale):
    HEADER = ['Sequence', 'BD-Rate (%)', 'Speed-Up', 'Time Reduction (%)']

    widths = dict()
    widths['sequence'] = len(HEADER[0])
    widths['bdrate'] = len(HEADER[1])
    widths['speedup'] = len(HEADER[2])
    widths['time_reduction'] = len(HEADER[3])

    for category, category_sequences in sequences.items():
        for sequence in category_sequences:
            widths['sequence'] = max(widths['sequence'], len(sequence))
            widths['bdrate'] = max(widths['bdrate'], len('{bdrate:>.{scale}f}'.format(bdrate = results[sequence]['bdrate'], scale = scale)))
            widths['speedup'] = max(widths['speedup'], len('{speedup:>.{scale}f}'.format(speedup = results[sequence]['speedup'], scale = scale)))
            widths['time_reduction'] = max(widths['time_reduction'], len('{time_reduction:>.{scale}f}'.format(time_reduction = results[sequence]['time_reduction'] * 100, scale = scale)))

    print('{sequence:<{sequence_width}}  {bdrate:>{bdrate_width}}  {speedup:>{speedup_width}}  {time_reduction:>{time_reduction_width}}'.format(sequence = HEADER[0], bdrate = HEADER[1], speedup = HEADER[2], time_reduction = HEADER[3], sequence_width = widths['sequence'], bdrate_width = widths['bdrate'], speedup_width = widths['speedup'], time_reduction_width = widths['time_reduction']))
    print('{line_content:=<{line_width}}'.format(line_content = '', line_width = sum(widths.values()) + 2 * (len(widths.values()) - 1)))

    for category, category_sequences in sequences.items():
        print('{line_content:-<{line_width}}'.format(line_content = '-- {} --'.format(category), line_width = sum(widths.values()) + 2 * (len(widths.values()) - 1)))
        for sequence in category_sequences:
            print('{sequence:{sequence_width}}  {bdrate:>{bdrate_width}.{scale}f}  {speedup:>{speedup_width}.{scale}f}  {time_reduction:>{time_reduction_width}.{scale}f}'.format(sequence = sequence, bdrate = results[sequence]['bdrate'], speedup = results[sequence]['speedup'], time_reduction = results[sequence]['time_reduction'] * 100, sequence_width = widths['sequence'], bdrate_width = widths['bdrate'], speedup_width = widths['speedup'], time_reduction_width = widths['time_reduction'], scale = scale))

    print('{line_content:=<{line_width}}'.format(line_content = '', line_width = sum(widths.values()) + 2 * (len(widths.values()) - 1)))
    print('{sequence:{sequence_width}}  {bdrate:>{bdrate_width}.{scale}f}  {speedup:>{speedup_width}.{scale}f}  {time_reduction:>{time_reduction_width}.{scale}f}'.format(sequence = 'Average', bdrate = average['bdrate'], speedup = average['speedup'], time_reduction = average['time_reduction'] * 100, sequence_width = widths['sequence'], bdrate_width = widths['bdrate'], speedup_width = widths['speedup'], time_reduction_width = widths['time_reduction'], scale = scale))

def main(argv):
    arguments = parse_arguments(argv[1:])

    base_results = hevctools.parser.parse_dir(arguments.base_path[0], arguments.base_pattern[0])
    test_results = hevctools.parser.parse_dir(arguments.test_path[0], arguments.test_pattern[0])
    sequences = sort_sequences(set(base_results.keys() & test_results.keys()))

    results, average = calculate_results(sequences, base_results, test_results, arguments.use_old_bdrate)

    print_results(sequences, results, average, arguments.scale[0])

if __name__ == "__main__":
    main(sys.argv)
