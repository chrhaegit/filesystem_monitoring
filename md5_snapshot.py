from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

class MD5Snapshot:

    MD5HASHES_FILENAME = ".md5_hashes.txt"
    SNAPSHOT_HYSTORY_DIR = Path.cwd() / "system" / "checksum_snapshots"
    SNAPSHOT_IN_PROGRESS_FILE_NAME = "xxxx-inprogress.json"
    SNAPSHOT_IN_PROGRESS_FILE_PATH = SNAPSHOT_HYSTORY_DIR / SNAPSHOT_IN_PROGRESS_FILE_NAME

    STATUS = ["INIT", "FILE_LIST", "IN_PROGRESS", "DONE"]

    def __init__(self):
        self._nrof_saves = 0
        
        if Path(MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH).exists():
            self.read_json_snapshot(MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH)
        else:
            self._snapshot = {"file_name" : MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH, 
                              "status" : "INIT", 
                              "files" : {}
                              }  

    def create_md5_from_file(self, file_path:Path, chunk_size=4096) -> str:
        """Calculate the MD5 hash of a file."""
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                md5.update(chunk)
        return md5.hexdigest()   
    
    def create_md5_from_string(self, data:str):
        md5 = hashlib.md5(data)
        return md5.hexdigest()
    
    """
        If the md5hashlist_file is not existing --> it will be created (empty file).
    """
    def get_dict_from_md5hashes_file(self, md5hashlist_filepath:Path):
        filelist = {}
        if md5hashlist_filepath.exists():                        
            with open(md5hashlist_filepath, "r", encoding='utf-8') as f:
                for line in f:
                    file_path, md5_hash_value = line.strip().split(": ")
                    filelist[file_path] = md5_hash_value
        return filelist  
    
    def get_missing_md5hashes_for_subdirs(self, rootdir:Path):
        # Traverse destination-tree and check if MD5-hashes exists in each directory in 
        # a file called '.md5_hashes.txt'. 
        # If it is not found, it will be created (if there are files in this folder)
        # If the file is found, the function checks, if all the hashes for all the files in the current 
        # folder are the '.md5_hashes.txt'. 
        # --> The ones which are missing are collected and given back in a list.
        missinglist = []
        for dir, _, files in os.walk(rootdir):
            dir_path = Path(dir)
            md5hashlist_filepath = dir_path / MD5Snapshot.MD5HASHES_FILENAME    
            
            filelist = {}
            if len(files) > 0:
                if not md5hashlist_filepath.exists():
                    # Create a new file:
                    with open(md5hashlist_filepath, 'w', encoding='utf-8') as _:
                        pass
                filelist = self.get_dict_from_md5hashes_file(md5hashlist_filepath)

            for curr_file in files:
                if curr_file != MD5Snapshot.MD5HASHES_FILENAME and curr_file not in filelist:
                    missinglist.append(dir_path / curr_file)
        return missinglist    
    
    def write_md5hashes_file(self, md5hashes_filename:Path, file_hashes:dict):
        if len(file_hashes) == 0: 
            return
        with open(md5hashes_filename, "w", encoding='utf-8') as f:
            for filename, file_hash in file_hashes.items():
                f.write(f"{filename}: {file_hash}\n")  

    def add_entry_to_md5hash_file(self, md5hashes_filename:Path, file_path:Path):
        file_hash = self.create_md5_from_file(file_path)
        with open(md5hashes_filename, "a", encoding='utf-8') as f:
            f.write(f"{file_path.name}: {file_hash}\n")  
    
    def create_md5hashes_for_filelist(self, filelist:list) -> float:
        start_time = time.time()   
        for fp in filelist:
            filepath = Path(fp)
            if not filepath.exists():
                raise FileNotFoundError(f"File from filelist not found: {filepath}")

            parent_folder = filepath.parent
            md5hashes_filename = parent_folder / MD5Snapshot.MD5HASHES_FILENAME    
            self.add_entry_to_md5hash_file(md5hashes_filename, filepath)

        runtime = time.time() - start_time
        return runtime
    
    def create_md5hashes_for_tree(self, rootdir:Path, overwrite=False, only_one_dir=False) -> tuple:
        """
            Traverse the directory and subdirectories, creating '.md5_hashes.txt' 
            with key: value-painrs: filename: md5-hash.
            return: runtime in milliseconds
        """
        start_time = time.time()   
        totalbytes = 0  
        for dir, _, files in os.walk(rootdir):
            dir_path = Path(dir)
            file_hashes = {}
            for filename in files:
                if filename == MD5Snapshot.MD5HASHES_FILENAME:  #dont create checksum for it
                    continue
                file_path = dir_path / filename
                totalbytes = totalbytes + file_path.stat().st_size
                file_hashes[filename] = self.create_md5_from_file(file_path)
            
            md5hashes_filename = dir_path / MD5Snapshot.MD5HASHES_FILENAME
            # if overwrite is false --> first check if the '.md5_hashes.txt' already exists:
            if overwrite == False and md5hashes_filename.exists():
                raise FileExistsError(f"md5hashes-filename already exists: {md5hashes_filename}")    
                
            self.write_md5hashes_file(md5hashes_filename, file_hashes)

            if only_one_dir: 
                break  # --> not walking down the tree ... finishing after the work on top-dir.

        runtime = time.time() - start_time
        return (runtime, totalbytes)
    

    
    def create_md5_snapshot(self, rootdir:Path) -> tuple:
        start_time = time.time()   
        totalbytes = 0  
        self.create_md5_snapshot_files(rootdir)

        tmp_counter = 0
        total_counter = 0
        for file_name, md5 in self._snapshot["files"].items():
            total_counter += 1
            if md5 != "xxx":
                continue    # already done in a previous run

            file_path = Path(file_name)
            totalbytes = totalbytes + file_path.stat().st_size
            md5_val = self.create_md5_from_file(file_path)
            self._snapshot["files"][file_name] = md5_val 
            tmp_counter += 1
            if tmp_counter >= 5:
                self._snapshot["status"] = "IN_PROGRESS"
                self.save_json_snapshot() 
                tmp_counter = 0

        dest = MD5Snapshot.SNAPSHOT_HYSTORY_DIR / self.get_snapshot_filename()
        self._snapshot["file_name"] = dest.as_posix()
        self._snapshot["status"] = "DONE"    
        self.save_json_snapshot()   
  
        if os.path.exists(MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH): 
            os.remove(MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH)
            print(f"In-Progress-File '{MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH}' deleted successfully.")
        else: 
            print(f"File '{MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH}' not found.")
        
        runtime = time.time() - start_time
        seconds = int(runtime)
        milliseconds = int((runtime - seconds) * 1000) 
        print(f"Runtime: {seconds}.{milliseconds:03d} seconds")
        self._snapshot["runtime"] = f"{seconds}.{milliseconds:03d}"
        self._snapshot["total_byte_size"] = f"{totalbytes:,}".replace(",", "'")
        return (runtime, totalbytes)
    
    def create_md5_snapshot_files(self, rootdir: Path):  
        if self._snapshot["status"] in ["FILE_LIST", "IN_PROGRESS", "DONE"]:
            return
                
        for dir, _, files in os.walk(rootdir):
            dir_path = Path(dir)
            for filename in files:
                if filename == MD5Snapshot.MD5HASHES_FILENAME:  #dont create checksum for it
                    continue
                file_path = dir_path / filename               
                self._snapshot["files"][file_path.as_posix()] = "xxx"
        self._snapshot["status"] = "FILE_LIST"  
        self._snapshot["file_name"] = MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH.as_posix()
        self.save_json_snapshot()    
    
    def get_snapshot_history_file_list(self):
        dir = Path(MD5Snapshot.SNAPSHOT_HYSTORY_DIR)
        retlist = []
        for f in dir.iterdir():
            if f.is_file() and f.name[0:4].isnumeric():
                retlist.append(f.name)
        return retlist
    
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
        
        for filename in os.listdir(MD5Snapshot.SNAPSHOT_HYSTORY_DIR):
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
 
    def read_json_snapshot(self, file:Path):        
        with open(file, "r",  encoding='utf-8') as f:
            self._snapshot = json.load(f)
    
    def save_json_snapshot(self):
        if len(self._snapshot) == 0: 
            return
        with open(self._snapshot["file_name"], "w", encoding='utf-8') as f:
            json.dump(self._snapshot, f, ensure_ascii=False, indent=4)
            self._nrof_saves += 1

    def create_md5hashes_for_dir(self, dir_path:Path, overwrite=False) -> tuple:
        return self.create_md5hashes_for_tree(dir_path, overwrite, only_one_dir=True)
    
    def checksum_validation_for_dir(self, dir:Path) -> tuple:
        start_time = time.time() 
        md5hashes_filename = dir / MD5Snapshot.MD5HASHES_FILENAME 

        missmatches = {}
         # Load expected hashes from .md5_hashes.txt --> the file will be created if not found!
        expected_hashes = self.get_dict_from_md5hashes_file(md5hashes_filename)          
        
        # Check each file's MD5 against the expected value
        for file_name, expected_md5 in expected_hashes.items():
            file_path = dir / file_name
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_name}' listed in 'md5_hashes.txt' does not exist in the destination.")

            actual_md5 = self.create_md5_from_file(file_path)
            if actual_md5 != expected_md5:
                missmatches[file_name] = (expected_md5, actual_md5)
                print(f"Checksum mismatch for file '{file_name}' in '{dir}': expected {expected_md5}, got {actual_md5}")
        runtime = time.time() - start_time
        return (runtime, missmatches)
    
    def checksum_validation_for_tree(self, rootdir: Path) -> tuple:
        start_time = time.time() 
          
        for curdir, dirs, files in os.walk(rootdir):
            md5hashes_filename = Path(curdir) / MD5Snapshot.MD5HASHES_FILENAME 
            missmatches = {}
            # Load expected hashes from .md5_hashes.txt --> the file will be created if not found!
            expected_hashes = self.get_dict_from_md5hashes_file(md5hashes_filename)    

            # Check each file's MD5 against the expected value
            for file_name, expected_md5 in expected_hashes.items():
                file_path = Path(curdir) / file_name
                if not file_path.exists():
                    raise FileNotFoundError(f"File '{file_name}' listed in 'md5_hashes.txt' does not exist in {curdir}")

                actual_md5 = self.create_md5_from_file(file_path)
                if actual_md5 != expected_md5:
                    missmatches[file_name] = (expected_md5, actual_md5)
                    print(f"Checksum mismatch for file '{file_name}' in '{dir}': expected {expected_md5}, got {actual_md5}")
            # end for
        # end walk
        runtime = time.time() - start_time
        return (runtime, missmatches)                      

def main():
    print("main(): start ...")
    src = r"C:\tmp\testsrc"
    helper = MD5Snapshot()

    #runtime = helper.create_md5hashes_for_subdirs(src, overwrite=True)

    # misslist = helper.get_missing_md5hashes_for_subdirs(src)
    # print(f"Number of missing hashes: {len(misslist)}")
    # for m in misslist:
    #     print(m)
    # runtime = helper.create_md5hashes_for_filelist(misslist)

    # runtime, fails = helper.checksum_validation_for_dir(Path(src) / "unicode_validation")
    # print(f"Total checksum violations: {len(fails)}")
    # for f, hashes in fails.items():
    #     print(f"{str(f).ljust(40, '.')} old={hashes[0]}")
    #     print(f"{str(f).ljust(40, '.')} new={hashes[1]}")

    testpath = Path(r"D:\Games\Overwolf")
    # testpath = Path(r"D:\_privat\projekte\GUIFormExamples")
    runtime, bytes = helper.create_md5hashes_for_tree(testpath, overwrite=True)
    
    print(f"Runtime: --- {runtime:.3f} seconds.  Bytes={bytes}")  
    print("main(): all done")
    
def create_snapshot():
    src = r"C:\tmp\testsrc"
    snapshot = MD5Snapshot()
    snapshot.create_md5_snapshot(src)


if __name__ == "__main__":
    # main()
    create_snapshot()