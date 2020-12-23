import json
import os
import pathlib
from datetime import datetime
from math import ceil
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

        if args.write:
            self.file_for_write   = args.write[0]
            self.path_where_write = args.write[1]
            self.file_entity      = {}

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

        self.__init_entities()

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
        if entity is None:
            print('[!] File or dir not exist')
            exit(0)

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

        # Parse fat record
        counter = clusters[0]
        val = counter
        N = clusters[0]
        if self.fs_type == 'FAT16':
            while val != 0xFFFF:
                val = int.from_bytes(self.data[self.f_fat_table + counter*2:self.f_fat_table+(counter+1)*2], 'little') & 0xFFFF
                counter += 1
                clusters.append(val)

                # For deleted files restore just one sector
                # TODO: think about that
                if entity['isDeleted'] == True:
                    break

                if len(clusters) < int(entity['Size']) / self.cluster_size and val == 0xFFFF:
                    clusters.pop()
                    val = 0
        elif self.fs_type == 'FAT12':
            # counter = 0
            while N != 0x11:
                offset = N + N // 2
                bits = self.data[self.f_fat_table + N: self.f_fat_table + offset]
                print(bits)

                # don't work
                if N & 1:
                    print(hex(bits[0]), hex(bits[1]))
                    cluster = ((bits[1] & 0xFF) << 4) % 0x100 | bits[0] & 0xf0
                    # cluster = bits[0] >> 4 | (bits[1] << 4)
                    # cluster = (bits[1] & 0x0f) << 8 | bits[0] & 0xff
                else:
                    print(hex(bits[0]), hex(bits[1]))
                    # cluster = (bits[1] & 0xff) << 8 | (bits[0] & 0xf0) >> 4
                    cluster = bits[0] | ((bits[1] & 0x0f) << 8)

                print('get cluster', hex(cluster)) 
                # exit(0)
                N += 1
                val = cluster
                # clusters.append(cluster)

                # # For deleted files restore just one sector
                # # TODO: think about that
                # if entity['isDeleted'] == True:
                #     break

                # if len(clusters) < int(entity['Size']) / self.cluster_size and val == 0xFFFF:
                #     clusters.pop()
                #     val = 0

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
        http://elm-chan.org/docs/fat_e.html#fat_determination
        """
        self.file_entity = {
            "Type": "f",
            "8DOT3Name": "",
            'Name' : "",
            'Size' : 0,
            'CreateTime' : "",
            'Cluster' : "",
            'isDeleted' : False
        }

        fname = pathlib.Path(self.file_for_write)
        if not fname.exists():
            print('[!] File for write in FAT not exists')
            exit(0)
        
        # get base info about file
        fstat = fname.stat()
        # filename
        filename = fname.parts[-1]
        if len(filename) > 8:
            short_name = (filename[:6] + '~1' + fname.suffix[1:4].ljust(3, ' ')).upper()
        else:
            short_name = filename.upper().ljust(8, ' ')

        # file size
        size = fstat.st_size
        # fat_time 
        modification_time = self.__convert_date_to_fat(datetime.fromtimestamp(fstat.st_mtime))
        last_access = self.__convert_date_to_fat(datetime.fromtimestamp(fstat.st_atime))
        status_change = self.__convert_date_to_fat(datetime.fromtimestamp(fstat.st_ctime))

        self.file_entity.update({
            "8DOT3Name": short_name,
            'Name': filename,
            'Size' : size,
            'ModificationTime' : modification_time,
            'LastAccessTime' : last_access,
            'StatusChangeTime' : status_change
        })

        """
        need get free cluster, if filesize > 0x800 than allocate new clasters in fat table
        else put in fat 0xffff
        """
        print(self.file_entity)
        # craft fat table
        cluster = self.__edit_fat_tables()
        self.file_entity.update({'Cluster': hex(cluster)})

        self.__craft_record(cluster)

        # make record in some sectors

    def __craft_record(self, cluster: int) -> None:
        bits = [1, 3, 5, 7, 9, 14, 16, 18, 20, 22, 24, 28, 30]
        count_records = ceil(len(self.file_entity['Name']) / 15)

        # template
        template = [0x43,0x74,0x00,0x00,0x00,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0x0F,0x00,0xB0,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0x00,0x00,0xFF,0xFF,0xFF,0xFF]
        
        if len(self.file_entity['Name']) >= 15:
            print('ok craft long name')

        tmp = []
        lfn_sum = self.__create_sum(self.file_entity['8DOT3Name'])

        # craft template for long name
        k = 0
        print('count records', count_records)
        for i in range(1, count_records + 1):
            if i == count_records:
                template[0] = 0x40 + i
            else:
                template[0] = i

            template[13] = lfn_sum

            for j, bit in enumerate(bits):
                string = self.file_entity['Name']
                if k >= len(string):
                    template[bit] = 0xFF
                else:
                    template[bit] = ord(string[k])
                k += 1

            tmp.append(b''.join([bytes([x]) for x in template]))
        
        print(tmp)
        out = b''.join(tmp[::-1])
        print(out)

        # init template for short name
        out += self.file_entity['8DOT3Name'].encode()   #name
        out += bytes([self.FILE_ATTRIBUTE])             #file attr
        out += b'\x00'                                  #reserved byte
        out += b'\x64'                                  #crt_time_tenth optional
        out += int.to_bytes(self.file_entity['ModificationTime'], 2, 'little')
        out += int.to_bytes(self.file_entity['StatusChangeTime'], 2, 'little')
        out += int.to_bytes(self.file_entity['LastAccessTime'], 2, 'little')
        out += b'\x00\x00'
        out += int.to_bytes(self.file_entity['ModificationTime'], 2, 'little')
        out += int.to_bytes(self.file_entity['ModificationTime'], 2, 'little')
        out += int.to_bytes(cluster, 2, 'little')
        out += int.to_bytes(self.file_entity['Size'], 4, 'little')

        BS = 32
        i = 0
        record = -1
        while record != 0x00:
            record = self.data[self.root_addr + BS*i]
            i += 1

        i -= 1        

        data = list(self.data)
        for j, el in enumerate(out):
            data[self.root_addr + BS*i + j] = out[j]
        
        print('writing to table')
        with open(self.file_for_write, 'rb') as f:
            file_data = f.read()
        
        for i, el in enumerate(file_data):
            data[self.data_addr + (cluster - 2)*self.cluster_size + i] = file_data[i]

        self.data = bytes(data)
        with open('shitfat.img', 'wb') as f:
            f.write(self.data)

        print('file created')

    def __create_sum(self, name) -> int:
        s = 0
        for el in name:
            s = ((s >> 1) + (s << 7) + ord(el) ) % 0x100
        return s

    def __edit_fat_tables(self) -> int:
        fat = self.data[self.f_fat_table: self.f_fat_table + self.fat_size]

        if self.fs_type == 'FAT16':
            new_record = fat.rindex(b'\xff\xff') + 2

            free_cluster = new_record // 0x2 + 1
            if self.file_entity['Size'] > self.cluster_size:
                clusters = int.to_bytes(free_cluster, 2, 'little')
                for i in range(free_cluster, free_cluster + self.file_entity['Size'] // self.cluster_size):
                    clusters += int.to_bytes(i, 2, 'little')
                clusters += b'\xff\xff'
            else:
                clusters = b'\xff\xff'

            data = list(self.data)

            for i in range(len(clusters)):
                data[self.f_fat_table + new_record + i] = clusters[i]
                data[self.s_fat_table + new_record + i] = clusters[i]
        elif self.fs_type == 'FAT12':
            new_record = fat.rindex(b'\xff\x0f') + 1
            free_cluster = fat[new_record] // 3
            print('free', free_cluster)

            if self.file_entity['Size'] > self.cluster_size:
                clusters = int.to_bytes(free_cluster, 2, 'little')
                for i in range(free_cluster, free_cluster + self.file_entity['Size'] // self.cluster_size):
                    print(clusters)
                    clusters += int.to_bytes(i, 2, 'little')
                clusters += b'\xff\xff\x0f'
            else:
                clusters = b'\xff\x0f'

            data = list(self.data)

            for i in range(len(clusters)):
                data[self.f_fat_table + new_record + i] = clusters[i]
                data[self.s_fat_table + new_record + i] = clusters[i]
            
            free_cluster += 1

        elif self.fs_type == 'FAT32':
            print('not realized')
            exit(0)
        
        self.data = bytes(data)
        print('done')
        return free_cluster - 1
        # path = [x for x in self.path_where_write.split('/') if x]

    def __create_folder_entry(self) -> None:
        """
        """
        pass

    # Fix this time isn't correct
    def __convert_date_to_fat(self, objdate) -> int:
        num = ((objdate.year - 80) << 25) % 0x10000 | \
              ((objdate.month + 1) << 21)% 0x10000 | \
              (objdate.day << 16)% 0x10000 |       \
              (objdate.hour << 11)% 0x10000 |      \
              (objdate.minute << 5)% 0x10000 |     \
              (objdate.second >> 1)% 0x10000
        return num
