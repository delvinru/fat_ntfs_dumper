from datetime import datetime
import os
import json
from string import printable


class FAT(object):
    def __init__(self, args):
        with open(args.file, 'rb') as f:
            data = f.read()
        
        self.FILE_ATTRIBUTE   = 0x20
        self.DIR_ATTRIBUTE    = 0x10

        self.catalog          = args.list
        self.json             = args.json
        self.extract          = args.extract
        self.show_deleted     = args.deleted
        self.create_file      = args.write

        self.data             = data
        self.oem              = self.data[0x3:0xB].decode()
        self.sector_size      = int.from_bytes(data[0xB:0xD], 'little')
        self.cluster_size     = self.sector_size * data[0xD]
        self.reserved_sectors = int.from_bytes(data[0xE:0x10], 'little')
        self.number_of_fat    = data[0x10]
        self.number_of_root   = int.from_bytes(data[0x11:0x13], 'little')
        self.fat_size         = self.sector_size * int.from_bytes(data[0x16:0x18], 'little')
        self.fs_type          = data[0x36:0x3B].decode()
        self.f_fat_table      = self.reserved_sectors*self.sector_size
        self.s_fat_table      = self.f_fat_table + self.fat_size
        self.root_addr        = self.s_fat_table + self.fat_size
        self.data_addr        = self.root_addr + (self.number_of_root * 0x20)
        self.files            = [] 
        self.tmp              = []

    def print_info(self) -> None:
        info =   'Информация о файловой системе\n\n'
        info += f'Имя OEM: {self.oem}\n'
        info += f'Размер сектора: {hex(self.sector_size)}\n'
        info += f'Размер кластера: {hex(self.cluster_size)}\n'
        info += f'Количество зарезервированных секторов: {hex(self.reserved_sectors)}\n'
        info += f'Количество таблиц FAT: {hex(self.number_of_fat)}\n'
        info += f'Количество записей корневой директории: {hex(self.number_of_root)}\n'
        info += f'Размер одной таблицы FAT: {hex(self.fat_size)}\n'
        info += f'Тип файловой системы: {self.fs_type}\n'
        info += f'Адрес таблицы FAT1: {hex(self.f_fat_table)}\n'
        info += f'Адрес таблицы FAT2: {hex(self.s_fat_table)}\n'
        info += f'Адрес корневой директории: {hex(self.root_addr)}\n'
        info += f'Адрес начала данных: {hex(self.data_addr)}'

        print(info)
    
    def print_catalogs(self) -> None:
        """List specified catalog"""

        self.__init_entities()
        path = [x for x in self.catalog.split('/') if x]

        if self.json:
            print(json.dumps(self.files))
            exit(0)

        if len(path) == 0:
            self.__print_entity(self.files)
            exit(0)
        else:
            entity = self.__find_entity_by_path(path, self.files)
            self.__print_entity(entity)
            exit(0)

    def __find_entity_by_path(self, path: list, entities: dict):
        """Internal function for recursive find entity in self.files dict"""

        for entity in entities:
            if entity['Name'] == path[0]:
                if entity['Name'] == path[0]:
                    path.pop(0)
                    
                    if len(path) == 0:
                        return entity

                    return self.__find_entity_by_path(path, entity['Elements'])
    
    def __print_entity(self, entity) -> None:
        """Just print specified catalog or entity"""

        if not self.extract:
            print('Listing:', self.catalog, end='\n\n')
        if type(entity) == dict:
            try:
                if entity['Type'] == 'f':
                    self.__extract_entity(entity)
                    exit(0)
            except TypeError:
                print('[!] File not exist')
                exit(0)

            try:
                if entity['Type'] == 'd':
                    entity = entity['Elements']
            except TypeError:
                print('[!] Directory not exists!')
                exit(0)

        for el in entity:
            directory = ''
            isdeleted = ''

            if el['isDeleted']:
                if not self.show_deleted:
                    continue
                isdeleted = ' (File deleted)'

            if el['Type'] == 'd':
                directory = '/'
            info  = f"{el['Type']} {el['CreateTime']} {el['Name']}{directory} ({el['8DOT3Name']}) Cluster:{el['Cluster']} Size:{el['Size']}{isdeleted}"
            print(info)
    
    def __extract_entity(self, entity) -> None:
        clusters = [int(entity['Cluster'], 16)]
        # f_addr = self.data_addr + self.cluster_size * (int(entity['Cluster'], 16) - 2)

        # Parse fat record
        counter = clusters[0]
        val = counter
        while val != 0xFFFF:
            val = self.data[self.f_fat_table + counter*2:self.f_fat_table+(counter+1)*2]
            counter += 1
            val = int.from_bytes(val, 'little') & 0xFFFF
            clusters.append(val)

            # For deleted files restore just one sector
            # TODO: think about that
            if entity['isDeleted'] == True:
                break

            if len(clusters) < int(entity['Size']) / self.cluster_size and val == 0xFFFF:
                clusters.pop()
                val = 0

        # Remove 0xFFFF in end of sectors list
        clusters.pop()
        file_data = b''

        # Read entity
        remaing_data = int(entity['Size'])
        for cluster in clusters:
            f_addr = self.data_addr + self.cluster_size * (cluster - 2)

            if remaing_data > self.cluster_size:
                s_addr = f_addr + self.cluster_size
            else:
                s_addr = f_addr + remaing_data

            remaing_data -= self.cluster_size
            file_data += self.data[f_addr : s_addr]
        
        if len(file_data) > 1024 or self.extract:
            if not os.path.exists('extracted/'):
                os.mkdir('extracted')
            with open('extracted/'+entity['Name'], 'wb') as f:
                f.write(file_data)

            print(f'File {entity["Name"]} was save in extracted/')
        else:
            print(file_data)

    def __parse_dir(self, start_addr: int, subdir: bool) -> None:
        BS = 32
        entry = []
        RA = start_addr
        i = 0
        deletedfile = b''

        # Read root catalog
        while True:
            count = self.data[RA+BS*i]

            if count == 0xE5:
                deletedfile += self.data[RA + BS*i: RA + BS*(i+1)]
                i += 1
                continue
            
            if deletedfile != b'':
                entry.append(deletedfile)
                deletedfile = b''

            if count == 0x2E:
                # hidden dir
                pass

            if count == 0:
                break

            if count > 0x40:
                # file with 0x41, 0x42 and others bytes
                entry.append(self.data[RA + BS*i: RA + BS*(i+count-0x3F)])
                i += (count - 0x3F)
            else:
                entry.append(self.data[RA + BS*i: RA + BS*(i+1)])
                i += 1

        self.__parse_file_entinity(entry, subdir)

    def __parse_file_entinity(self, entry : list, subdir: bool) -> None:
        for el in entry:
            long_name  = ''
            is_deleted = False

            if el[0] == 0xE5:
                is_deleted = True

            filetype  = self.__get_type(el)
            time      = self.__get_time(el)
            shortname = self.__get_name(el)
            size      = self.__get_size(el)
            cluster   = self.__get_cluster(el)

            if len(el)//32 == 1:
                long_name = shortname.lower()
            else:
                long_name = self.__get_long_name(el)
            
            parent_obj = {
                "Type": filetype,
                "8DOT3Name": shortname,
                'Name' : long_name,
                'Size' : size,
                'CreateTime' : time,
                'Cluster' : cluster,
                'isDeleted' : is_deleted
            }

            if filetype == 'd':
                parent_obj.update({'Elements': []})
                if not subdir:
                    self.files.append(parent_obj)
                else:
                    self.tmp.append(parent_obj)
            else:
                if not subdir:
                    self.files.append(parent_obj)
                else:
                    self.tmp.append(parent_obj)

    def __init_entities(self) -> None:
        """Init all entities in file system to json dict, for nice work"""

        # parse root directory
        self.__parse_dir(self.root_addr, False)

        def recursive_parse_dir(entity: dict):
            for element in entity:
                if element.get('Elements') == []:
                    if element['Name'] == '.' or element['Name'] == '..':
                        continue

                    self.__parse_dir(self.data_addr + self.cluster_size * (int(element['Cluster'], 16) - 2), True)
                    element.update({
                        'Elements': self.tmp
                    })
                    self.tmp = []
                    recursive_parse_dir(element['Elements'])
            return entity
            
        # parse others directory
        self.files = recursive_parse_dir(self.files)
        
    def __get_cluster(self, file) -> str:
        """Extract data cluster from file"""

        return hex(int.from_bytes(file[-6:-4], 'little'))

    def __get_name(self, file) -> str:
        """Extract file name"""

        name = file[-32:-21]
        # remove non printable characher
        fpart = ''.join(list(filter(lambda x: x in printable, name[:8].rstrip().decode(errors='ignore'))))
        lpart = ''.join(list(filter(lambda x: x in printable, name[8:].rstrip().decode(errors='ignore'))))
        if not len(lpart):
            return fpart
        else:
            return fpart + '.' + lpart

    def __get_long_name(self, file) -> str:
        """Extract long file name"""

        BS = 32
        bits = [1, 3, 5, 7, 9, 14, 16, 18, 20, 22, 24, 28, 30]
        name = b''
        blocks = [file[i*BS:BS*(i+1)] for i in range(len(file)//BS)]
        for el in blocks[::-1][1:]:
            for bit in bits:
                name += bytes([el[bit]])

        return name.replace(b'\xff',b'').replace(b'\x00', b'').decode()

    def __get_time(self, file) -> str:
        """Extract time from file"""

        date_creation = int.from_bytes(file[-16:-14], 'little')

        day   = str(date_creation & 0x1f)
        month = str((date_creation>>5) & 0x0f)
        year  = str(1980 + (date_creation >> 9))

        return day + '-' + month + '-' + year
    
    def __get_type(self, file) -> str:
        """Detect type of file"""

        attr =  file[-21]
        if attr == self.DIR_ATTRIBUTE:
            return 'd'
        elif attr == self.FILE_ATTRIBUTE:
            return 'f'
        else:
            return '?'
    
    def __get_size(self, file) -> str:
    
        """Extract file size"""

        size = int.from_bytes(file[-4:-1], 'little')
        return str(size)
    
    def write_file(self) -> None:
        """
        For write file need change FAT1 and FAT2
        Make record in root directory or in subdirectory
        That's all?

        Maybe delete --create <dir>
        We should goes through all directories in self.files and if folder not exist,
        create folder, after this we should create file_entry
        Steps:
        1. If dir not exists create folder_entry
        2. Create file_entry in this directory
        3. Done

        http://elm-chan.org/docs/fat_e.html#fat_determination
        """

        pass

    def __create_folder_entry(self) -> None:
        """
        """
        pass