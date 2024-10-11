import json
import logging
import logging.config
import os
from pathlib import Path
import time

from md5dir import MD5Dir
from snapshot import Snapshot

class MD5Snapshot (Snapshot):

    SNAPSHOT_HYSTORY_DIR = Path.cwd() / "system" / "checksum_snapshots"
    SNAPSHOT_IN_PROGRESS_FILE_NAME = "xxxx-inprogress.json"
    SNAPSHOT_IN_PROGRESS_FILE_PATH = SNAPSHOT_HYSTORY_DIR / SNAPSHOT_IN_PROGRESS_FILE_NAME
    STATUS = ["INIT", "FILE_LIST", "IN_PROGRESS", "DONE"]
    PROGRESS_STEP_SIZE = 1_000_000_000

    def __init__(self, log:logging.Logger):
        Snapshot.__init__(self, MD5Snapshot.SNAPSHOT_HYSTORY_DIR, "-md5.json")
        self.log = log
        if self._snapshot["status"] == "INIT":
            self._snapshot["nroffiles"] = 0
            self._snapshot["totalbytes"] = 0 
            self._snapshot["runtime"] = 0
            self._snapshot["runtime seconds"] = "Runtime: 0 seconds"
            self._snapshot["files"] = {}
            self._nroffiles = 0
            self._totalbytes = 0
            self._runtime = 0.0
        else:
            self._nroffiles = int(self._snapshot["nroffiles"])
            self._totalbytes = int(str(self._snapshot["totalbytes"]).replace("'", ""))
            self._runtime = float(self._snapshot["runtime"])

    @property
    def runtime(self):
        return self._runtime

    @property
    def runtime_str(self):
        return self._snapshot["runtime seconds"]
    
    @property
    def totalbytes(self):
        return self._totalbytes

    def __str__(self):
        return f"{self._nroffiles=} {self._totalbytes=}{self.runtime_str=}"                             
    
    def create_md5_snapshot(self, rootdir:Path) -> tuple:
        start_time = time.time()   
        self.create_md5_snapshot_files(rootdir)

        tmp_byte_count = 0
        for file_name, md5 in self._snapshot["files"].items():            
            if md5 != "xxx":
                continue    # already done in a previous run

            file_path = Path(file_name)
            tmp_byte_count += file_path.stat().st_size
            self._totalbytes += file_path.stat().st_size
            self._nroffiles += 1
            md5_val = MD5Dir.create_md5_from_file(file_path)
            self._snapshot["files"][file_name] = md5_val 
            
            if tmp_byte_count >= MD5Snapshot.PROGRESS_STEP_SIZE:
                self.update_file_infos("IN_PROGRESS")
                self._runtime = self._runtime + (time.time() - start_time)               
                self.save_snapshot() 

                tmp_byte_count = 0
                start_time = time.time() 

        dest = MD5Snapshot.SNAPSHOT_HYSTORY_DIR / self.create_new_snapshot_filename()
        self._snapshot["file_name"] = dest.as_posix()
        self.update_file_infos("DONE")
  
        if os.path.exists(MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH): 
            os.remove(MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH)
            print(f"In-Progress-File '{MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH}' deleted successfully.")
        else: 
            print(f"File '{MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH}' not found.")
    
    def create_md5_snapshot_files(self, rootdir: Path):  
        if self._snapshot["status"] in ["FILE_LIST", "IN_PROGRESS", "DONE"]:
            return
                
        for dir, _, files in os.walk(rootdir):
            dir_path = Path(dir)
            for filename in files:
                file_path = dir_path / filename               
                self._snapshot["files"][file_path.as_posix()] = "xxx"
        self._snapshot["status"] = "FILE_LIST"  
        self._snapshot["file_name"] = MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH.as_posix()
        self.save_snapshot()    

    def update_file_infos(self, status:str):
        self._snapshot["runtime"] = self._runtime
        self._snapshot["runtime seconds"] = self.get_formatted_runtime_str()
        self._snapshot["totalbytes"] = f"{self._totalbytes:,}".replace(",", "'")
        self._snapshot["nroffiles"] = self._nroffiles
        self._snapshot["status"] = status    
        self.save_snapshot()  
        self.log.info(f"updated snapshot infos: {self}")


    def get_formatted_runtime_str(self)->str:        
        seconds = int(self._runtime)
        milliseconds = int((self._runtime - seconds) * 1000) 
        return f"Runtime: {seconds}.{milliseconds:03d} seconds"
                  

def main():
    # ****** logging init ***********
    with open("logging.json", "r") as f:
        log_config = json.load(f)
        logging.config.dictConfig(log_config)
    log = logging.getLogger(os.path.basename(__file__))

    log.info("main(): start ...")
    src = r"C:\tmp\testsrc"
    src = r"D:\Games\Overwolf"  
    src = r"D:\Games\World_of_Tanks"
    snap = MD5Snapshot(log)

    snap.create_md5_snapshot(src)
    log.info(f"created snapshot")
    log.info(f"Runtime: --- {snap.runtime_str} sec, bytes={snap.totalbytes}")
    log.info(f"sec/GB={(snap.runtime/snap.totalbytes*1_000_000_000):.3f}")
    log.info("main(): all done")

if __name__ == "__main__":
    main()