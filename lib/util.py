import lib.fat as fat

def get_info_about_filesystem(filename: str) -> str:
    with open(filename, 'rb') as f:
        data = f.read(64)
    
    name = data[0x36:0x3B]
    if b'NTFS' in name:
        name = data[0x03:0x7]
        # ntfs.print_info(filename)
    elif b'FAT' in name:
        fat.print_info(filename, True)
    

def get_info_about_catalogs(filename: str) -> None:
    table = fat.print_info(filename, False)
    if 'FAT' in table['name']:
        fat.print_catalogs(filename, table)
        pass
    else:
        print('Not recognized filesystem')
        exit(0)