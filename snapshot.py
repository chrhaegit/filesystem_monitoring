from datetime import datetime
import json
import os
from pathlib import Path


class Snapshot:

    SNAPSHOT_IN_PROGRESS_FILE_NAME = "xxxx-inprogress.json"

    def __init__(self, history_dir:Path, snapshot_filename_ending:str):
        self._nrof_saves = 0
        self._history_dir = history_dir
        self._snapshot_filename_ending = snapshot_filename_ending

        if Path(self.snapshot_in_progress_file_path).exists():
            self.load_snapshot(self.snapshot_in_progress_file_path)
        else:
            self._snapshot = {"file_name" : self.snapshot_in_progress_file_path, 
                              "status" : "INIT"                            
                             }         
        
    @property
    def snapshot_in_progress_file_path(self) -> Path: 
        return self._history_dir / Snapshot.SNAPSHOT_IN_PROGRESS_FILE_NAME
    

    def get_snapshot_history_file_list(self) -> list[str]:       
        retlist = []
        for f in self._history_dir.iterdir():
            if f.is_file() and f.name[0:4].isnumeric():
                retlist.append(f.name)
        return retlist
    
    def get_last_snapshot_number(self):
        history_list = self.get_snapshot_history_file_list()
        biggest_nr = 0
        for fn in history_list:
            if fn[0:4].isnumeric():
                nr = int (fn[0:4])
                if nr > biggest_nr:
                    biggest_nr = nr           
        return biggest_nr    
    
    def get_last_snapshot_filename(self):
        highest_number = -1
        last_snapshot_filename = None
        
        for filename in os.listdir(self._history_dir):
            # Check if the filename matches the pattern 'xxxx-JJJJMMDD-VS.json'
            if filename.endswith('-VS.json') and len(filename) == 21 and filename[:4].isdigit():            
                file_number = int(filename[:4])
                if file_number > highest_number:
                    highest_number = file_number
                    last_snapshot_filename = filename
        return last_snapshot_filename      
    
    def create_new_snapshot_filename(self):
        strdate = f"{datetime.now().year}{datetime.now().month:02d}{datetime.now().day:02d}"
        next_snapshot_nr = self.get_last_snapshot_number() + 1
        return f"{next_snapshot_nr:04d}-{strdate}-VS.json"

    def load_snapshot(self, file:Path):        
        with open(file, "r",  encoding='utf-8') as f:
            self._snapshot = json.load(f)
    
    def save_snapshot(self):
        if len(self._snapshot) == 0: 
            return
        with open(self._snapshot_file_name, "w", encoding='utf-8') as f:
            json.dump(self._snapshot, f, ensure_ascii=False, indent=4)
            self._nrof_saves += 1        

def main():
    print("main(): start ...")
    history_dir = Path.cwd() / "system" / "checksum_snapshots"
    snapshot = Snapshot(history_dir, "VS")

    print(f"last snapshot number: {snapshot.get_last_snapshot_number()}")
    print(f"last snapshot: {snapshot.get_last_snapshot_filename()}")
    for f in snapshot.get_snapshot_history_file_list():
        print(f)

    s2 = Snapshot(history_dir, "VS")
    s2.load_snapshot("D:/_privat/projekte/python/filesystem_monitoring/system/checksum_snapshots/0006-20241003-VS.json")
    print(f"{s2._snapshot["file_name"]=}")
    print(f"{s2._snapshot["status"]=}")
    print("main(): all done")
    
if __name__ == "__main__":
    main()           