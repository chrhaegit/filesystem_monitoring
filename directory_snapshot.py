import json
import os
from pathlib import Path
import time
from datetime import datetime

class DirectorySnapshot:

    SNAPSHOT_HYSTORY_DIR = Path.cwd() / "system" / "directorystructure_snapshots"

    def __init__(self, rootDir:Path):
        self._rootdir = rootDir
        self.create_snapshot(self._rootdir)
        self.write_json_snapshot()

    @property
    def snapshot(self):
        return self._snapshot

    def create_snapshot(self, rootdir:Path, overwrite=False, only_one_dir=False) -> tuple:
        start_time = time.time()   
        self._snapshot = {}
        totalbytes = 0  
        for dir, subdirs, files in os.walk(rootdir):
            dir_path = Path(dir)
            self._snapshot[dir_path] = [len(files), "DIR"]
            
            for filename in files:
                if filename.startswith("."):  #don't put it in the snapshot 
                    continue
                file_path = dir_path / filename
                file_size = file_path.stat().st_size
                totalbytes = totalbytes + file_size
                self._snapshot[file_path] = [file_size, "FILE"]

            if only_one_dir: 
                break  # not walking down the tree ... just snapsthot from the rootdir.

        runtime = time.time() - start_time
        return (runtime, totalbytes)
    
    def get_last_snapshot_number(self):
        history_list = self.get_snapshot_history_file_list()
        biggest_nr = 0
        for fn in history_list:
            nr = int (fn[0:5])
            if nr > biggest_nr:
                biggest_nr = nr
            print(fn)
        return biggest_nr 

    def get_snapshot_history_file_list(self):
        return [p.name for p in Path(DirectorySnapshot.SNAPSHOT_HYSTORY_DIR).iterdir() if p.is_file()]
    
    def get_snapshot_filename(self):        
        strdate = f"{datetime.now().year}{datetime.now().month}{datetime.now().day}"
        next_snapshot_nr = self.get_last_snapshot_number() + 1
        return f"{next_snapshot_nr : 05d}-{strdate}-VS.json"
    
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


def main():
    print("main(): start ...")
    src = r"C:\tmp\testsrc"
    snapshot = DirectorySnapshot(src)
    
    # print(snapshot.get_last_snapshot_number())
    # print(snapshot.get_snapshot_filename())
    
    print(snapshot.snapshot)
    #runtime = helper.create_md5hashes_for_subdirs(src, overwrite=True)
    # print(f"Runtime: --- {runtime:.3f} seconds.  Bytes={bytes}")  
    print("main(): all done")
    
if __name__ == "__main__":
    main()