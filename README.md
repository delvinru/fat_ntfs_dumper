# fat_ntfs_dumper
Utility for analyzing FAT(12,16,32) and NTFS file systems
(while work FAT)

The program can display a list of files, view the contents for any FAT12,FAT16 files, also shows a list of deleted files and partially restores them.
It is possible to write data to the FAT16 file system, writing to FAT12 is not implemented.

# Install

```bash
git clone https://github.com/delvinru/fat_ntfs_dumper.git
cd fat_ntfs_dumper/
python3 main.py
```

# Usage
```bash
usage: main.py [-h] -f FILE [-i] [-l <file> or <dir>] [-j] [-e] [-d] [-w <from> <to>]

Help menu for program

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Provide file for analyze
  -i, --info            Print info about filesystem
  -l <file> or <dir>, --list <file> or <dir>
                        Print info about existing files
  -j, --json            Print data in json
  -e, --extract         Extract file or files from path
  -d, --deleted         Show deleted files
  -w <from> <to>, --write <from> <to>
                        Write file to file system (ONLY FAT16)
                        Argument takes two args:
                        1 where i should read data; 2 where should I put the data

Examples:
Print info about root directory:
python3 main.py -f testfile.img -l /

Print info about files in catalog:
python3 main.py -f testfile.img -l /somecatalog/

Extract file from path:
python3 main.py -f testfile.img -l /somefile.txt -e
python3 main.py -f testfile.img -l /catalog/somefile.txt -e
```