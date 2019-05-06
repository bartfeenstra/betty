import argparse
import sys

from betty import parse, render
from betty.config import from_file
from betty.site import Site


def generate(config_file_path: str):
    with open(config_file_path) as f:
        configuration = from_file(f)
    with Site(configuration) as site:
        parse.parse(site)
        render.render(site)


def build_parser():
    parser = argparse.ArgumentParser(
        description='Betty is a static ancestry site generator.')
    subparsers = parser.add_subparsers()
    generate_parser = subparsers.add_parser(
        'generate', description='Generate a static site.')
    generate_parser.add_argument('--config', dest='config_file_path',
                                 required=True, action='store')
    generate_parser.set_defaults(_callback=generate)
    return parser


def main(args=None):
    try:
        parser = build_parser()
        parsed_args = vars(parser.parse_args(args))
        if '_callback' not in parsed_args:
            parser.print_usage(sys.stderr)
            parser.exit(2)
        callback = parsed_args['_callback']
        del parsed_args['_callback']
        callback(**parsed_args)
    except KeyboardInterrupt:
        # Quit gracefully.
        print('Quitting...')
