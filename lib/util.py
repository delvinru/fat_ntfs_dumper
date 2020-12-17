from lib.fat import *

def get_info_about_filesystem(args: dict) -> str:
    with open(args.file, 'rb') as f:
        data = f.read(64)
    
    name = data[0x36:0x3B]
    if b'NTFS' in name:
        name = data[0x03:0x7]
        # ntfs.print_info(filename)
    elif b'FAT' in name:
        FAT(args).print_info()
    

def get_info_about_catalogs(args: dict) -> None:
    obj = FAT(args)
    obj.print_catalogs()