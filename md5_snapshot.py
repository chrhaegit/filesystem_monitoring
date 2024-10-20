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
    
    PROGRESS_STEP_SIZE = 1_000_000_000

    def __init__(self, log:logging.Logger):
        Snapshot.__init__(self, "-md5.json")

        config = Snapshot.readjson_config()
        if config and "SNAPSHOT_HYSTORY_DIR" in config :
            Snapshot.HYSTORY_DIR = config["SNAPSHOT_HYSTORY_DIR"]
            self.log.info(f"monitoring_config.json: set HYSTORY_DIR={Snapshot.HYSTORY_DIR}")
        else:
            Snapshot.HYSTORY_DIR = Path.cwd() / "system" / "directorystructure_snapshots"

        self.log = log
        if self.status != "INIT":
            self.nroffiles = Snapshot.get_nroffiles_from_snapshot()
            self.totalbytes = Snapshot.get_totalbytes_from_snapshot()
            self.runtime = Snapshot.get_runtime_from_snapshot()
              
    
    def create_md5_snapshot(self, rootdir:Path) -> tuple:
        start_time = time.time()   
        self.create_md5_snapshot_files(rootdir)
        tmp_byte_count = 0
        for file_name, md5 in self._snapshot["files"].items():            
            if md5 != "xxx":
                continue    # already done in a previous run
            file_path = Path(file_name)
            tmp_byte_count += file_path.stat().st_size
            self.totalbytes += file_path.stat().st_size
            self.nroffiles += 1
            md5_val = MD5Dir.create_md5_from_file(file_path)
            self._snapshot["files"][file_name] = md5_val             
            if tmp_byte_count >= MD5Snapshot.PROGRESS_STEP_SIZE:
                self.update_file_infos("IN_PROGRESS")
                self._runtime = self._runtime + (time.time() - start_time)               
                self.save_snapshot() 

                tmp_byte_count = 0
                start_time = time.time() 
        # end for-loop
        dest = MD5Snapshot.SNAPSHOT_HYSTORY_DIR / self.create_new_snapshot_filename()
        self._snapshot["file_name"] = dest.as_posix()
        self.update_file_infos("DONE")
  
        if os.path.exists(MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH): 
            os.remove(MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH)
            print(f"In-Progress-File '{MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH}' deleted successfully.")
        else: 
            print(f"File '{MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH}' not found.")
    
    def create_md5_snapshot_files(self, rootdir: Path):  
        if self.status in ["FILE_LIST", "IN_PROGRESS", "DONE"]:
            return
                
        for dir, _, files in os.walk(rootdir):
            dir_path = Path(dir)
            for filename in files:
                file_path = dir_path / filename               
                self._snapshot["files"][file_path.as_posix()] = "xxx"
        self.status = "FILE_LIST"  
        self._snapshot["file_name"] = MD5Snapshot.SNAPSHOT_IN_PROGRESS_FILE_PATH.as_posix()
        self.save_snapshot()                      

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