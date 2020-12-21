import argparse
import sys

from lib.util import *

def main(args):
    if args.list:
        get_info_about_catalogs(args)
        exit(0)

    if args.info:
        get_info_about_filesystem(args)
        exit(0)
    

if __name__ == "__main__":

    usage = """Examples:
Print info about root directory:
python3 main.py -f testfile.img -l /

Print info about files in catalog:
python3 main.py -f testfile.img -l /somecatalog/

Extract file from path:
python3 main.py -f testfile.img -l /somefile.txt -e
python3 main.py -f testfile.img -l /catalog/somefile.txt -e
"""
    parser = argparse.ArgumentParser(
        description='Help menu for program',
        epilog = usage,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-f', '--file',
        required=True,
        type=str,
        help='Provide file for analyze'
    )

    parser.add_argument(
        '-t', '--type',
        help='Provide file system version'
    )

    parser.add_argument(
        '-i', '--info',
        action='store_true',
        help='Print info about filesystem'
    )

    parser.add_argument(
        '-l', '--list',
        metavar="<file> or <dir>",
        help='Print info about existing files'
    )

    parser.add_argument(
        '-j', '--json',
        action='store_true',
        help='Print data in json'
    )

    parser.add_argument(
        '-e', '--extract',
        action='store_true',
        help='Extract file or files from path'
    )

    parser.add_argument(
        '-r', '--restore',
        action='store_true',
        help='Restore deleted files'
    )

    if len(sys.argv) < 2:
        parser.print_help()
        exit(0)

    args = parser.parse_args()

    # Run main function
    main(args)