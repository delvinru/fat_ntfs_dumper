from lib.fat import *

def get_info_about_filesystem(filename: str) -> str:
    with open(filename, 'rb') as f:
        data = f.read(64)
    
    name = data[0x36:0x3B]
    if b'NTFS' in name:
        name = data[0x03:0x7]
        # ntfs.print_info(filename)
    elif b'FAT' in name:
        FAT(filename).print_info()
    

def get_info_about_catalogs(filename: str) -> None:
    obj = FAT(filename)
    obj.print_catalogs()