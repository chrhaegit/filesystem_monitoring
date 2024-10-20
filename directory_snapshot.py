import copy
import glob
import json
import logging
import os
from pathlib import Path
import time
from datetime import datetime
from snapshot import Snapshot

class DirectorySnapshot:

    def __init__(self, log:logging.Logger, rootDir:Path):
        Snapshot.__init__(self, "-VS.json")  
        self.log = log
        self._rootdir = rootDir
        self._snapshot = {"elements":[]}

        config = Snapshot.readjson_config()
        if config and "DIRECTORY_HYSTORY_DIR" in config :
            Snapshot.HYSTORY_DIR = config["DIRECTORY_HYSTORY_DIR"]
            self.log.info(f"monitoring_config.json: set DIRECTORY_HYSTORY_DIR={Snapshot.HYSTORY_DIR}")
        else:
            Snapshot.HYSTORY_DIR = Path.cwd() / "system" / "directorystructure_snapshots"

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
        search_pattern = os.path.join(Snapshot.HYSTORY_DIR, f"{number:04d}-*-VS.json")
        matching_files = glob.glob(search_pattern)
        if matching_files: 
            self.read_json_snapshot_file(matching_files[0])
    
    def load_last_snapshot(self):
        file_path = Snapshot.HYSTORY_DIR / Snapshot.get_last_snapshot_filename() 
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
    
    def get_snapshot_filename(self):        
        strdate = f"{datetime.now().year}{datetime.now().month:02d}{datetime.now().day:02d}"
        next_snapshot_nr = Snapshot.get_last_snapshot_number() + 1
        return f"{next_snapshot_nr:04d}-{strdate}-VS.json"
    

    def read_json_snapshot_file(self, file_path: Path):   
        with open(file_path, "r",  encoding='utf-8') as fn:
            self._snapshot = json.load(fn)


def main():
    print("main(): start ...")    
    # ****** logging init ***********
    with open("logging.json", "r") as f:
        log_config = json.load(f)
        logging.config.dictConfig(log_config)
    log = logging.getLogger(os.path.basename(__file__))
    
    # create_snapshot()
    print_snapshots(log)

    #runtime = helper.create_md5hashes_for_subdirs(src, overwrite=True)
    # print(f"Runtime: --- {runtime:.3f} seconds.  Bytes={bytes}")  
    print("main(): all done")

def create_snapshot():
    print("main(): start ...")   
    # ****** logging init ***********
    with open("logging.json", "r") as f:
        log_config = json.load(f)
        logging.config.dictConfig(log_config)
    log = logging.getLogger(os.path.basename(__file__))

    src = r"C:\tmp\testsrc"
    src = r"D:\Games\World_of_Tanks"
    snapshot = DirectorySnapshot(log, src)
    runtime, totalbytes = snapshot.create_snapshot()
    #snapshot.save_snapshot()

    print(f"Runtime: --- {runtime:.3f} seconds.  Bytes={totalbytes}")  
    print("main(): all done")

def print_snapshots(log:logging.Logger):
    src = r"C:\tmp\testsrc"
    src = r"D:\Games\World_of_Tanks"
    last_snapshot = DirectorySnapshot(log, src)
    last_snapshot.load_last_snapshot()
    second_snapshot = DirectorySnapshot(log, src)
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
    # main()
    create_snapshot()