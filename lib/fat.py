def print_info(filename:str, check: bool) -> None:
    """
    Functions that print all useful information about FAT(X) img
    """
    with open(filename, 'rb') as f:
        data = f.read(64)

    ss = int.from_bytes(data[0xB:0xD], 'little')
    table_info = {
        'sector_size':      int.from_bytes(data[0xB:0xD], 'little'),
        'cluster_size':     ss * data[0xD],
        'reserved_sectors': int.from_bytes(data[0xE:0x10], 'little'),
        'number_of_fat':    data[0x10],
        'number_of_root':   int.from_bytes(data[0x11:0x13], 'little'),
        'mft_size':         ss * int.from_bytes(data[0x16:0x18], 'little'),
        'fs_type':          data[0x36:0x3B].decode(),
    }
    table_info.update(
        {
            'f_addr_table': table_info['reserved_sectors']*table_info['sector_size']
        }
    )

    table_info.update(
        {
            's_addr_table': table_info['f_addr_table']+table_info['mft_size'],
        }
    )

    table_info.update(
        {
            'root_addr':    table_info['s_addr_table']+table_info['mft_size']
        }
    )

    info  = f'Размер сектора: {hex(table_info["sector_size"])}\n'
    info += f'Размер кластера: {hex(table_info["cluster_size"])}\n'
    info += f'Количество зарезервированных секторов: {hex(table_info["reserved_sectors"])}\n'
    info += f'Количество таблиц FAT: {hex(table_info["number_of_fat"])}\n'
    info += f'Количество записей корневой директории: {hex(table_info["number_of_root"])}\n'
    info += f'Размер одной таблицы FAT: {hex(table_info["mft_size"])}\n'
    info += f'Тип файловой системы: {table_info["fs_type"]}\n\n'
    info += f'Адрес первой таблицы FAT: {hex(table_info["f_addr_table"])}\n'
    info += f'Адрес второй таблицы FAT: {hex(table_info["s_addr_table"])}\n'
    info += f'Адрес корневой директории: {hex(table_info["root_addr"])}'


    if check:
        print(info)
    else:
        return table_info

def print_catalogs(filename: str, table_info: dict) -> None:
    # TODO: print tree of files in img
    with open(filename, 'rb') as f:
        data = f.read()
        
    pass
    