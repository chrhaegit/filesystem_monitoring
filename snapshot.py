from datetime import datetime
import json
import logging
import os
from pathlib import Path


class Snapshot:

    HYSTORY_DIR = Path.cwd()
    SNAPSHOT_IN_PROGRESS_FILE_NAME = "xxxx-inprogress.json"
    STATUS = ["INIT", "FILE_LIST", "IN_PROGRESS", "DONE"]

    def __init__(self, snapshot_filename_ending:str):
        self.log = logging.getLogger(os.path.basename(__file__))

        self._nrof_saves = 0
        self._snapshot_filename_ending = snapshot_filename_ending

        if Path(self.snapshot_in_progress_file_path).exists():
            self._snapshot_filename = "TODO"
            self.load_snapshot(self.snapshot_in_progress_file_path)
              
        else:
            self._snapshot = {"file_name" : self.snapshot_in_progress_file_path, 
                                "status" : "INIT",         
                                "nroffiles" : 0,
                                "totalbytes" : 0, 
                                "runtime" : 0,
                                "runtime seconds" : "Runtime: 0 seconds",               
                             }   
                
    def load_snapshot(self, file:Path):        
        with open(file, "r",  encoding='utf-8') as f:
            self._snapshot = json.load(f)

        self.status = self._snapshot["status"]  
        self.nroffiles = Snapshot.get_nroffiles_from_snapshot()
        self.totalbytes = Snapshot.get_totalbytes_from_snapshot()
        self.runtime = Snapshot.get_runtime_from_snapshot() 

    #region properties
    @property
    def status(self):
        return self._status
    @status.setter
    def status(self, newval):
        if newval not in Snapshot.STATUS:
            raise ValueError(f"invalid status: {newval}") 
        self._status = newval
            
    @property
    def runtime(self):
        return self._runtime
    @runtime.setter
    def runtime(self, newval):
        self._runtime = newval

    @property
    def runtime_str(self):
        return self._snapshot["runtime seconds"]
    
    @property
    def nroffiles(self):
        return self._nroffiles
    @nroffiles.setter
    def nrofffiles(self, newval:int):
        self._nroffiles = newval
    
    @property
    def totalbytes(self):
        return self._totalbytes
    @totalbytes.setter
    def totalbytes(self, newval):
        self._totalbytes = newval

    @property
    def snapshot_in_progress_file_path(self) -> Path: 
        return Snapshot.HYSTORY_DIR / Snapshot.SNAPSHOT_IN_PROGRESS_FILE_NAME
    #endregion properties

    def __str__(self):
        return f"{self._nroffiles=} {self._totalbytes=}{self.runtime_str=}" 
    
    def get_nroffiles_from_snapshot(self):
        return int(self._snapshot["nroffiles"])
    
    def get_totalbytes_from_snapshot(self) -> int:
        return int(str(self._snapshot["totalbytes"]).replace("'", ""))
    
    def get_runtime_from_snapshot(self) -> float:
        return float(self._snapshot["runtime"])

    def update_file_infos(self, status:str):
        self._snapshot["status"] = status   
        self._snapshot["runtime"] = self.runtime
        self._snapshot["runtime seconds"] = self.get_formatted_runtime_str()
        self._snapshot["totalbytes"] = f"{self._totalbytes:,}".replace(",", "'")
        self._snapshot["nroffiles"] = self.nroffiles
        self.save_snapshot()  
        self.log.info(f"updated snapshot infos: {self}")

    def get_formatted_runtime_str(self)->str:        
        seconds = int(self._runtime)
        milliseconds = int((self._runtime - seconds) * 1000) 
        return f"Runtime: {seconds}.{milliseconds:03d} seconds"

    def readjson_config(self):        
        data = {}
        config_fn = Path.cwd() / "monitoring_config.json"
        if not Path(self.snapshot_in_progress_file_path).exists():
            self.log.error(f"monitoring_config.json not found in {Path.cwd()} ")
            raise FileNotFoundError(config_fn)
        
        with open(config_fn, "r",  encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as json_decode_error:
                self.log.error(f"Could not decode json config file: {config_fn}")
                raise json_decode_error
        return data
    

    def get_snapshot_history_file_list(self) -> list[str]:       
        retlist = []
        for f in Snapshot.HYSTORY_DIR.iterdir():
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
        
        for filename in os.listdir(Snapshot.HYSTORY_DIR):            
            if filename.endswith(self._snapshot_filename_ending) and filename[:4].isdigit():            
                file_number = int(filename[:4])
                if file_number > highest_number:
                    highest_number = file_number
                    last_snapshot_filename = filename
        return last_snapshot_filename      
    
    def create_new_snapshot_filename(self) -> str:
        strdate = f"{datetime.now().year}{datetime.now().month:02d}{datetime.now().day:02d}"
        next_snapshot_nr = self.get_last_snapshot_number() + 1
        return f"{next_snapshot_nr:04d}-{strdate}{self._snapshot_filename_ending}"             
    
    def save_snapshot(self):
        if len(self._snapshot) == 0: 
            return
        with open(self._snapshot["file_name"], "w", encoding='utf-8') as f:
            json.dump(self._snapshot, f, ensure_ascii=False, indent=4)
            self._nrof_saves += 1
        self.log.debug(f"saved snapshot into file: {self._snapshot["file_name"]}")    

def main():
    print("main(): start ...")
    history_dir = Path.cwd() / "system" / "checksum_snapshots"
    snapshot = Snapshot(history_dir, "-md5.json")

    print(f"last snapshot number: {snapshot.get_last_snapshot_number()}")
    print(f"last snapshot: {snapshot.get_last_snapshot_filename()}")
    print(f"new snapshot filename: {snapshot.create_new_snapshot_filename()}")
    for f in snapshot.get_snapshot_history_file_list():
        print(f)

    s2 = Snapshot(history_dir, "-md5.json")
    s2.load_snapshot("D:/_privat/projekte/python/filesystem_monitoring/system/checksum_snapshots/0002-20241003-md5.json")
    print(f"{s2._snapshot["file_name"]=}")
    print(f"{s2._snapshot["status"]=}")
    print("main(): all done")
    
if __name__ == "__main__":
    main()           