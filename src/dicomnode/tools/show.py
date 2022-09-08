from argparse import _SubParsersAction, ArgumentParser, Namespace, ArgumentTypeError

from pathlib import Path
from dicomnode.lib.utils import str2bool
from dicomnode.lib.io import load_dicom, load_private_tags

from pprint import pprint

def get_parser(subparser : _SubParsersAction):
  _, _, tool_name = __name__.split(".")
  module_parser = subparser.add_parser(tool_name, help="Displays a dicom file")
  module_parser.add_argument('dicomfile', type=Path, help="Path to dicom file to be shown")
  module_parser.add_argument('--privatetags', type=Path, help="Path to .dlc file with private tags")
  module_parser.add_argument('--strictParsing', type=str2bool, nargs='?', const=False, default=False, help="Stop if a private tag is not parsed correctly")

def entry_func(args : Namespace):
  privateTags = None
  if args.privatetags:
    load_private_tags(args.privatetags)

  pprint(load_dicom(args.dicomfile, private_tags=privateTags))