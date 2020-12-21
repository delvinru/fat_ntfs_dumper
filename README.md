# fat_ntfs_dumper
Utility for analyzing FAT(12,16,32) and NTFS file systems
(while work FAT)

# Install

```bash
git clone https://github.com/delvinru/fat_ntfs_dumper.git
cd fat_ntfs_dumper/
python3 main.py
```

# Usage
```bash
usage: main.py [-h] -f FILE [-t TYPE] [-i] [-l <file> or <dir>] [-j] [-e] [-r]

Help menu for program

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Provide file for analyze
  -t TYPE, --type TYPE  Provide file system version
  -i, --info            Print info about filesystem
  -l <file> or <dir>, --list <file> or <dir>
                        Print info about existing files
  -j, --json            Print data in json
  -e, --extract         Extract file or files from path
  -r, --restore         Restore deleted files

Examples:
Print info about root directory:
python3 main.py -f testfile.img -l /

Print info about files in catalog:
python3 main.py -f testfile.img -l /somecatalog/

Extract file from path:
python3 main.py -f testfile.img -l /somefile.txt -e
python3 main.py -f testfile.img -l /catalog/somefile.txt -ee
```