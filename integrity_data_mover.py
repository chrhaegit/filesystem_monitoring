import os
from pathlib import Path
import shutil
from md5_snapshot import MD5Snapshot 

class IntegrityDataMover:

    def __init__(self, src:str, dest:str):
        self._md5helper = MD5Snapshot()
        self._md5list_filename = "md5_hashes.txt"

        self._sourcepath = Path(src)
        if not self._sourcepath.exists() :
            print(f"Source-Pfad {src} existiert nicht!")
            raise AttributeError(f"Source-Pfad {src} existiert nicht!")
        
        self._destpath = Path(dest)
        if not self._destpath.exists() :
            print(f"Destination-Pfad {dest} existiert nicht!")
            raise AttributeError(f"Destination-Pfad {dest} existiert nicht!")
        print("1) ok .. src and dest Pfade existieren.")

        
        if self._sourcepath.is_dir():
            print("2) src-Pfad ist ein directory")            
        else:
            print("2) src-Pfad ist ein directory")

    @property
    def sourcepath(self):
        return self._sourcepath
    @property
    def destpath(self):
        return self._destpath

    def copy_tree(self):
        self.copy_src_to_dest(self._sourcepath, self._destpath)

    def copy_src_to_dest(self, srcdir: Path, destdir: Path):
        for item in srcdir.iterdir():
            dest_item = destdir / item.name
            
            # Copy the item (directory or file)
            if item.is_dir():
                shutil.copytree(item, dest_item)
            else:
                shutil.copy2(item, dest_item)

    def remove_source_content_only(self):
        # removing directory-structure        
        for filename in os.listdir(self.sourcepath): 
            tmp_path = self.sourcepath / filename  
            try:
                if tmp_path.is_file():
                    os.remove(tmp_path)  
                else:  
                    shutil.rmtree(tmp_path)
            except Exception as e:  
                print(f"Error deleting {tmp_path}: {e}")
        print("remove_source() done")        
        
    def collect_existing_items_in_destination(self): 
        # Pre-check: Collect existing files/directories in the destination
        existing_items = []
        for item in self._sourcepath.iterdir():
            dest_item = self._destpath / item.name
            if dest_item.exists():
                if dest_item.is_file():
                    existing_items.append(f"File:  {dest_item}")
                else: 
                    existing_items.append(f"Dir :  {dest_item}")
        return existing_items

def main():
    src = r"C:\tmp\testsrc"
    #src = "D:/_privat/projekte/python/filesystem_monitoring/testpfad"
    dest = r"D:\_privat\projekte\python\filesystem_monitoring\test_dest"
    idm = IntegrityDataMover(src, dest) 
    
    #idm.copy_tree()
    print("main(): all done")
    

if __name__ == "__main__":
    main()
   