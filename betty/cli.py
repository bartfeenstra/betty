import argparse

from betty.config import from_file
from betty.gramps import parse
from betty.render import render
from betty.site import Site


def main(args):
    parser = argparse.ArgumentParser(
        description='Betty is a static ancestry site generator.')
    parser.add_argument('--config', dest='config_file_path',
                        required=True, action='store')

    parsed_args = parser.parse_args(args)
    try:
        with open(parsed_args.config_file_path) as f:
            configuration = from_file(f)
        ancestry = parse(configuration.input_gramps_file_path)
        site = Site(ancestry, configuration)
        render(site)
    except KeyboardInterrupt:
        # Quit gracefully.
        print('Quitting...')
