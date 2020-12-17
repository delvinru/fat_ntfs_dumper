from datetime import datetime
import json


class FAT(object):
    def __init__(self, args):
        with open(args.file, 'rb') as f:
            data = f.read()
        
        self.FILE_ATTRIBUTE   = 0x20
        self.DIR_ATTRIBUTE    = 0x10

        self.catalog          = args.catalog
        self.json             = args.json

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
        self.files            = []

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
        self.__init_entity(self)

        if self.json:
            json.dumps(self.files)
        else:
            print('Listing catalog:', self.catalog)
            for el in self.files:
                info  = f"{el['Type']} {el['CreateTime']} {el['Name']} ({el['8DOT3Name']}) Cluster:{el['Cluster']} Size:{el['Size']} "
                if el['isDeleted']:
                    info += 'File deleted'
                print(info)

    def __init_entity(self, catalog):
        BS = 32
        entry = []
        RA = self.root_addr
        i = 0
        deletedfile = b''
        while True:
            count = self.data[RA+BS*i]

            if count == 0xE5:
                deletedfile += self.data[RA + BS*i: RA + BS*(i+1)]
                i += 1
                continue
            
            if deletedfile != b'':
                entry.append(deletedfile)
                deletedfile = b''

            if count == 0:
                break
            
            entry.append(self.data[RA + BS*i: RA + BS*(i+count-0x3F)])
            i += (count - 0x3F)
        
        self.__parse_file_entinity(entry)
        
    def __parse_file_entinity(self, entry):
        for el in entry:
            long_name  = False
            is_deleted = False

            if el[0] == 0xE5:
                is_deleted = True

            filetype  = self.__get_type(el)
            time      = self.__get_time(el)
            shortname = self.__get_name(el)
            size      = self.__get_size(el)
            cluster   = self.__get_cluster(el)

            if len(el)//32 == 2:
                long_name = shortname.lower()
            else:
                long_name = self.__get_long_name(el)


            self.files.append(
                {
                    "Type": filetype,
                    "8DOT3Name": shortname,
                    'Name' : long_name,
                    'Size' : size,
                    'CreateTime' : time,
                    'Cluster' : cluster,
                    'isDeleted' : is_deleted
                }
            )

    def __get_cluster(self, file):
        return hex(int.from_bytes(file[-6:-4], 'little'))

    def __get_name(self, file):
        name = file[-32:-21]
        sem = ''
        try:
            fpart = name[:8].rstrip().decode()
            lpart = name[8:].rstrip().decode()
            sem = '.'
        except:
            fpart = name[:8].rstrip()
            lpart = name[8:].rstrip()
            sem = b'.'
        if not len(lpart):
            return fpart
        else:
            return fpart + sem + lpart

    def __get_long_name(self, file):
        BS = 32
        bits = [1, 3, 5, 7, 9, 14, 16, 18, 20, 22, 24, 28, 30]
        name = b''
        blocks = [file[i*BS:BS*(i+1)] for i in range(len(file)//BS)]
        for el in blocks[::-1][1:]:
            for bit in bits:
                name += bytes([el[bit]])

        return name.replace(b'\xff',b'').decode()

    def __get_time(self, file):
        date_creation = int.from_bytes(file[-16:-14], 'little')

        day   = str(date_creation & 0x1f)
        month = str((date_creation>>5) & 0x0f)
        year  = str(1980 + (date_creation >> 9))

        return day + '-' + month + '-' + year
    
    def __get_type(self, file):
        attr =  file[-21]
        if attr == self.DIR_ATTRIBUTE:
            return 'd'
        elif attr == self.FILE_ATTRIBUTE:
            return 'f'
        else:
            return '?'
    
    def __get_size(self, file):
        size = int.from_bytes(file[-4:-1], 'little')
        return str(size)
    