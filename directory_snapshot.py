import copy
import glob
import json
import os
from pathlib import Path
import time
from datetime import datetime

class DirectorySnapshot:

    SNAPSHOT_HYSTORY_DIR = Path.cwd() / "system" / "directorystructure_snapshots"

    def __init__(self, rootDir:Path):
        self._rootdir = rootDir
        self._snapshot = {"elements":[]}

    @property
    def snapshot(self):
        return self._snapshot 
    
    def element_found(self, path_as_key: str):
        found = False
        for el in self._snapshot["elements"]:
           if el["path"] == path_as_key:
               found = True
               break
        return found

    def get_element_list(self, file_or_dir="ALL"):
        retlist = self._snapshot["elements"]
        if file_or_dir != "ALL":
            retlist = [el for el in self._snapshot["elements"] if el["type"] == file_or_dir ]
        return retlist 

    def create_snapshot(self, overwrite=False, only_one_dir=False) -> tuple:
        start_time = time.time()           
        totalbytes = 0  
        for dir, _, files in os.walk(self._rootdir):
            dir_path = Path(dir)
            self._snapshot["elements"].append(
                {"type" : "DIR", 
                 "path" : dir_path.as_posix(), 
                 "nrof_files" : len(files)
                 }) 
            
            for filename in files:
                if filename.startswith(".md5_hashes"):  #don't put it in the snapshot 
                    continue
                file_path = dir_path / filename
                nr_of_bytes = file_path.stat().st_size                               
                self._snapshot["elements"].append(
                    {"type" : "FILE", 
                     "path" : file_path.as_posix(), 
                     "file_length" : f"{nr_of_bytes:,}"
                    }) 

                totalbytes = totalbytes + nr_of_bytes
            if only_one_dir: 
                break  # stop walking down the tree ... just snapshot the rootdir.

        runtime = time.time() - start_time
        seconds = int(runtime)
        milliseconds = int((runtime - seconds) * 1000) 
        print(f"Runtime: {seconds}.{milliseconds:03d} seconds")
        self._snapshot["runtime"] = f"{seconds}.{milliseconds:03d}"
        self._snapshot["total_byte_size"] = f"{totalbytes:,}".replace(",", "'")
        return (runtime, totalbytes)
 
    def load_snapshot(self, number:int):
        search_pattern = os.path.join(DirectorySnapshot.SNAPSHOT_HYSTORY_DIR, f"{number:04d}-*-VS.json")
        matching_files = glob.glob(search_pattern)
        if matching_files: 
            self.read_json_snapshot_file(matching_files[0])
    
    def load_last_snapshot(self):
        file_path = DirectorySnapshot.SNAPSHOT_HYSTORY_DIR / self.get_last_snapshot_filename() 
        self.read_json_snapshot_file(file_path)
    
    def diff_snapshot(self, older_snapshot: 'DirectorySnapshot'):
        diff_list = {}
        deep_copied_older_snapshot = copy.deepcopy(older_snapshot.get_element_list())  
     
        for new_el in self.get_element_list():            
            path = new_el["path"]
            if not older_snapshot.element_found(path):
                diff_list[path] = "+"
            else:
                deep_copied_older_snapshot.remove(new_el)
        # see if there are elements in the older_snapshot which are not in the new one:
        for old_el in deep_copied_older_snapshot:
            path = old_el["path"]
            diff_list[path] = "-"

        return diff_list
    
    def get_snapshot_history_file_list(self):
        return [p.name for p in Path(DirectorySnapshot.SNAPSHOT_HYSTORY_DIR).iterdir() if p.is_file()]
    
    def get_last_snapshot_number(self):
        history_list = self.get_snapshot_history_file_list()
        biggest_nr = 0
        for fn in history_list:
            nr = int (fn[0:4])
            if nr > biggest_nr:
                biggest_nr = nr           
        return biggest_nr    
    
    def get_last_snapshot_filename(self):
        highest_number = -1
        last_snapshot_filename = None
        
        for filename in os.listdir(DirectorySnapshot.SNAPSHOT_HYSTORY_DIR):
            # Check if the filename matches the pattern 'xxxx-JJJJMMDD-VS.json'
            if filename.endswith('-VS.json') and len(filename) == 21 and filename[:4].isdigit():            
                file_number = int(filename[:4])
                if file_number > highest_number:
                    highest_number = file_number
                    last_snapshot_filename = filename
        return last_snapshot_filename      
    
    def get_snapshot_filename(self):        
        strdate = f"{datetime.now().year}{datetime.now().month:02d}{datetime.now().day:02d}"
        next_snapshot_nr = self.get_last_snapshot_number() + 1
        return f"{next_snapshot_nr:04d}-{strdate}-VS.json"
    
    def write_snapshot(self):
        self._snapshot_filename = DirectorySnapshot.SNAPSHOT_HYSTORY_DIR / self.get_snapshot_filename()
        if len(self._snapshot) == 0: 
            return
        with open(self._snapshot_filename, "w", encoding='utf-8') as f:
            for file_or_dir, list in self.snapshot.items():
                f.write(f"{file_or_dir}: {list}\n")      

    def write_json_snapshot(self):
        self._snapshot_filename = DirectorySnapshot.SNAPSHOT_HYSTORY_DIR / self.get_snapshot_filename()
        if len(self._snapshot) == 0: 
            return
        with open(self._snapshot_filename, "w", encoding='utf-8') as f:
            json.dump(self.snapshot, f, ensure_ascii=False, indent=4)

    def read_json_snapshot_file(self, file_path: Path):   
        with open(file_path, "r",  encoding='utf-8') as fn:
            self._snapshot = json.load(fn)


def main():
    print("main(): start ...")    
    # create_snapshot()
    print_snapshots()

    #runtime = helper.create_md5hashes_for_subdirs(src, overwrite=True)
    # print(f"Runtime: --- {runtime:.3f} seconds.  Bytes={bytes}")  
    print("main(): all done")

def create_snapshot():
    src = r"C:\tmp\testsrc"
    snapshot = DirectorySnapshot(src)
    snapshot.create_snapshot()
    snapshot.write_json_snapshot()

def print_snapshots():
    src = r"C:\tmp\testsrc"
    last_snapshot = DirectorySnapshot(src)
    last_snapshot.load_last_snapshot()
    second_snapshot = DirectorySnapshot(src)
    second_snapshot.load_snapshot(2)

    diff_list = last_snapshot.diff_snapshot(second_snapshot)
    for key, value in diff_list.items():
        print(f"{value} ¦ {key}")

    # for el in last_snapshot.get_element_list():
    #     print(el)

    # found = last_snapshot.element_found('C:/tmp/testsrc/unicode_validation/__pycache__/continuationbyte.cpython-312.pyc')
    # print(f"{found=}")

    # for el in second_snapshot.get_element_list():
    #     print(el)
    
if __name__ == "__main__":
    main()