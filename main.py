import argparse
import sys

from lib.util import *

def main(args):
    # Step 1
    if args.info:
        get_info_about_filesystem(args.file)
        exit(0)
    
    if args.catalog:
        get_info_about_catalogs(args)
        exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Help menu for program')

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
        '-c', '--catalog',
        help='Print info about existing files'
    )

    parser.add_argument(
        '-j', '--json',
        action='store_true',
        help='Print data in json'
    )

    args = parser.parse_args()
    if len(sys.argv) < 2:
        parser.print_help()
        exit(0)
    # Run main function
    main(args)