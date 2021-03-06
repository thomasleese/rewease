from collections import namedtuple
import json
from pathlib import Path
import subprocess

from cairosvg import svg2png


class IosIconsGenerator:

    """Generates approriate iOS icons for an app from an SVG file."""

    IMAGES = {
        'iphone': {
            20: [2, 3],
            29: [2, 3],
            40: [2, 3],
            60: [2, 3],
        },
        'ipad': {
            20: [1, 2],
            29: [1, 2],
            40: [1, 2],
            76: [1, 2],
            83.5: [2],
        },
        'ios-marketing': {
            1024: [1],
        },
    }
    """
    IMAGES is a dictionary for configuring the JSON output from this script. It
    is a mapping of idiom, to size, to scales.
    """

    INFO = {
        "version" : 1,
        "author" : "xcode",
    }
    """
    INFO is the dictionary that appears at the end of the JSON output from this
    script.
    """

    def __init__(self, input_file, output_folder):
        self.input_file = input_file
        self.output_folder = Path(output_folder)

    def __call__(self):
        self.write_contents_json()

    def write_contents_json(self):
        path = self.output_folder / 'Contents.json'
        config = self.build_contents_json_dictionary()
        with path.open('w') as file:
            file.write(json.dumps(config, sort_keys=True, indent=2))

    def build_images_dictionary(self):
        config = []

        for idiom, sizes in self.IMAGES.items():
            for size, scales in sizes.items():
                for scale in scales:
                    config.append({
                        'size': f'{size}x{size}',
                        'idiom': idiom,
                        'filename': self.save_png(size, scale),
                        'scale': f'{scale}x',
                    })

        return config

    def build_contents_json_dictionary(self):
        return {
            'images': self.build_images_dictionary(),
            'info': self.INFO,
        }

    def export_svg(self, path, size, scale, parent_size):
        output_scale = size / parent_size * scale

        svg2png(
            url=self.input_file,
            write_to=path,
            parent_width=parent_size,
            parent_height=parent_size,
            scale=output_scale,
        )

    def remove_alpha_channel(self, path):
        args = ['convert', path, '-alpha', 'off', path]
        subprocess.run(args, check=True)

    def compress_image(self, path):
        args = [
            'pngquant',
            '--quality=60-80',
            '--speed=1',
            '--force',
            '--strip',
            '--output', path,
            '--', path,
        ]

        subprocess.run(args, check=True)

    def save_png(self, size, scale, parent_size = 1024):
        filename = f'icon-{size}@{scale}.png'
        output_path = str(self.output_folder / filename)

        print(filename)

        self.export_svg(output_path, size, scale, parent_size)
        self.remove_alpha_channel(output_path)
        self.compress_image(output_path)

        return filename


def register(subparsers):
    def command(args):
        IosIconsGenerator(
            args.input_file, args.output_folder
        )()

    parser = subparsers.add_parser('ios-icons')
    parser.add_argument('input_file', type=str)
    parser.add_argument('output_folder', type=str)
    parser.set_defaults(func=command)
