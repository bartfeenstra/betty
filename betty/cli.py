import argparse

from betty.gramps import parse
from betty.render import render


def main(args):
    parser = argparse.ArgumentParser(
        description='Betty is a static ancestry site generator.')
    parser.add_argument('--input-gramps', dest='input_file_path_gramps', required=True, action='store')
    parser.add_argument('--output', dest='output_directory_path', required=True, action='store')

    parsed_args = parser.parse_args(args)
    try:
        ancestry = parse(parsed_args.input_file_path_gramps)
        render(ancestry, parsed_args.output_directory_path)
    except KeyboardInterrupt:
        # Quit gracefully.
        print('Quitting...')
