from pathlib import Path

from directory_snapshot import DirectorySnapshot
from md5_snapshot import MD5Snapshot


class IntegrityMonitoring:

    def __init__(self, src:Path):
        self._src = src
        self._dir_snapshot = DirectorySnapshot(self._src)
        self._md5_snapshot = MD5Snapshot(self._src)
        
    def create_new_directory_snapshot(self):        
        self._dir_snapshot.create_snapshot()
        self._dir_snapshot.write_json_snapshot()     

    def create_new_md5_snapshot(self):        
        self._md5_snapshot.create_md5_snapshot()
        self._dir_snapshot.write_json_snapshot()    

    def run():
        # 1. Create directory snapshot

        # 2. Create MD5 snapshot
        pass



def main():
    print("main(): start ...")
    src = r"C:\tmp\testsrc"
    monitor = IntegrityMonitoring(src)
    
    print("main(): all done")

if __name__ == "__main__":
    main()