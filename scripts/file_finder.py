import os
from collections import Counter

MAIN = r'\\10.0.0.3\raid\other\bignum'

class File:
    def __init__(self, const:str, base:int, format:str, size:int, path:str):
        self.const = const # str constant name eg. "Pi", "Euler's", "Sqrt(2)"
        self.base = base # int the base the number is written in eg. 2, 10, 16
        self.format = format # str file suffix/type eg. "txt", "ycd"
        self.size = size # int amount of digits after decimal eg. 1000000, 1000000000
        self.path = path # str eg. "/home/user/Pi - Dec - Chudnovsky.txt"

    def __getitem__(self, item):
        if item == 'const':
            return self.const
        elif item == 'base':
            return self.base
        elif item == 'format':
            return self.format
        elif item == 'size':
            return self.size
        elif item == 'path':
            return self.path
    
    def __repr__(self):
        return f'<{self.const}.{self.format}|b{self.base}|{self.size:.1E}>'

def get_files(main_path:str = MAIN):
    def get_infos(file_path:str):
        file_size = os.stat(file_path).st_size
        file_format =  file_path[-3:]
        file_name = os.path.split(file_path)[-1]

        if 'dec' in file_name.lower(): file_base = 10
        elif 'hex' in file_name.lower(): file_base = 16
        else:
            c = Counter(open(file_path).read(10000))
            del c['.']
            file_base = len(c)

        file_const = file_name.split('-')[0].split(' ')[0]
        return File(file_const, file_base, file_format, file_size, file_path)

    folders = os.listdir(main_path)
    ignore_list = ['.temp', 'y-cruncher']
    files:list[File] = []

    for folder in folders:
        if any((i in folder for i in ignore_list)): continue
        path = os.path.join(main_path, folder)
        for file in os.listdir(path):
            files.append(get_infos(os.path.join(path,file)))
    
    return files

def grouped(key:str, files:list[File] = None):
    if files is None:
        files = get_files()
    files_dict:dict[str,list[File]] = {}
    for file in files:
        if file[key] in files_dict:
            files_dict[file[key]].append(file)
        else:
            files_dict[file[key]] = [file]
    return [v for v in files_dict.values()]    

def one_of_each():
    """ ## get one of each constants
    
    guaranteed txt and base10

    used for base converting
    
    returns list of strings representing the path to the file"""
    files:list[File] = []
    for group in grouped('const'):
        sublist = filter(lambda x:x.format=='txt', group)
        sublist = filter(lambda x:x.base==10, sublist)
        try:
            files.append(next(sublist))
        except:
            continue
    return files

    # for key in keys:
    #     for group in grouped(key, group):
            
    # return [sorted(l,key=lambda x:x.size)[0] for l in grouped(key)]
    # return [sorted(l,key=lambda x:x.size,reverse=True)[0] for l in grouped(key)] # for getting biggest number available instead of smallest

    # files:list[File] = []
    # for group in grouped(key):
    #     if len(group) == 0: continue
    #     if len(group) == 1:
    #         files.append(group[0])
    #         continue
    #     if len(group) > 100:
    #         print('warning, found a lot of files')
    #     files.append(sorted(group, key=lambda x:x.size)[0])
    # return files

if __name__ == '__main__':
    print(list(one_of_each()))