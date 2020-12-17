class FAT(object):
    def __init__(self, filename):
        with open(filename, 'rb') as f:
            data = f.read()

        self.data             = data
        self.sector_size      = int.from_bytes(data[0xB:0xD], 'little')
        self.cluster_size     = self.sector_size * data[0xD]
        self.reserved_sectors = int.from_bytes(data[0xE:0x10], 'little')
        self.number_of_fat    = data[0x10]
        self.number_of_root   = int.from_bytes(data[0x11:0x13], 'little')
        self.mft_size         = self.sector_size * int.from_bytes(data[0x16:0x18], 'little')
        self.fs_type          = data[0x36:0x3B].decode()
        self.f_mft_table      = self.reserved_sectors*self.sector_size
        self.s_mft_table      = self.f_mft_table + self.mft_size
        self.root_addr        = self.s_mft_table + self.mft_size
        self.data_addr        = self.root_addr + (self.number_of_root * 0x20)
        self.files            = {}

    def print_info(self):
        info =   'Информация о файловой системе\n\n'
        info += f'Размер сектора: {hex(self.sector_size)}\n'
        info += f'Размер кластера: {hex(self.cluster_size)}\n'
        info += f'Количество зарезервированных секторов: {hex(self.reserved_sectors)}\n'
        info += f'Количество таблиц FAT: {hex(self.number_of_fat)}\n'
        info += f'Количество записей корневой директории: {hex(self.number_of_root)}\n'
        info += f'Размер одной таблицы FAT: {hex(self.mft_size)}\n'
        info += f'Тип файловой системы: {self.fs_type}\n'
        info += f'Адрес таблицы FAT1: {hex(self.f_mft_table)}\n'
        info += f'Адрес таблицы FAT2: {hex(self.s_mft_table)}\n'
        info += f'Адрес корневой директории: {hex(self.root_addr)}\n'
        info += f'Адрес начала данных: {hex(self.data_addr)}'

        print(info)
    
    def print_catalogs(self):
        BS = 32
        files = []
        RA = self.root_addr
        i = 0
        while True:
            count = self.data[RA+BS*i]
            if count == 0:
                break
            
            files.append(self.data[RA + BS*i: RA + BS*(i+count-0x3F)])
            i += (count - 0x3F)