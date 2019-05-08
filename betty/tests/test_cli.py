from json import dump
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from betty.cli import main
from betty.site import Site


class MainTest(TestCase):
    @patch('sys.stderr')
    def test_without_subcommand(self, _):
        with self.assertRaises(SystemExit):
            main()

    @patch('argparse.ArgumentParser')
    @patch('sys.stdout')
    def test_with_keyboard_interrupt(self, _, parser):
        parser.side_effect = KeyboardInterrupt
        main()

    @patch('betty.render.render')
    @patch('betty.parse.parse')
    def test_generate(self, parse, render):
        with NamedTemporaryFile(mode='w') as config_file:
            with TemporaryDirectory() as output_directory_path:
                url = 'https://example.com'
                config_dict = {
                    'output': output_directory_path,
                    'url': url,
                }
                dump(config_dict, config_file)
                config_file.seek(0)

                args = ['generate', '--config', config_file.name]
                main(args)

                self.assertEquals(1, parse.call_count)
                parse_args, parse_kwargs = parse.call_args
                self.assertEquals(1, len(parse_args))
                self.assertIsInstance(parse_args[0], Site)
                self.assertEquals({}, parse_kwargs)

                self.assertEquals(1, render.call_count)
                render_args, render_kwargs = render.call_args
                self.assertEquals(1, len(render_args))
                self.assertIsInstance(render_args[0], Site)
                self.assertEquals({}, render_kwargs)
