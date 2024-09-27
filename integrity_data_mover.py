from pathlib import Path
import shutil
from md5helper import MD5Helper 

class IntegrityDataMover:

    def __init__(self, src:str, dest:str):
        self._md5helper = MD5Helper()
        self._md5list_filename = "md5_hashes.txt"

        self._srcpath = Path(src)
        if not self._srcpath.exists() :
            print(f"Source-Pfad {src} existiert nicht!")
            raise AttributeError(f"Source-Pfad {src} existiert nicht!")
        
        self._destpath = Path(dest)
        if not self._destpath.exists() :
            print(f"Destination-Pfad {dest} existiert nicht!")
            raise AttributeError(f"Source-Pfad {dest} existiert nicht!")
        print("1) ok .. src and dest Pfade existieren.")

        
        if self._srcpath.is_dir():
            print("2) src-Pfad ist ein directory")            
        else:
            print("2) src-Pfad ist ein directory")

    def copy_tree(self):
        self.copy_src_to_dest(self._srcpath, self._destpath)

    def copy_src_to_dest(self, srcdir: Path, destdir: Path):
        """
        Copies the content of the source directory to the destination directory.
        The destination directory must already exist. If any file or directory
        from the source exists in the destination, the function raises an error
        before copying anything.

        Args:
        - srcdir (Path): The source directory path.
        - destdir (Path): The destination directory path.
        
        Raises:
        - ValueError: If the source directory does not exist, is not a directory, 
        or if the destination directory does not exist.
        - FileExistsError: If any file or directory from the source already exists in the destination.
        """
        if not srcdir.exists() or not srcdir.is_dir():
            raise ValueError(f"Source directory '{srcdir}' does not exist or is not a directory.")
        
        if not destdir.exists() or not destdir.is_dir():
            raise ValueError(f"Destination directory '{destdir}' does not exist or is not a directory.")
        
        # Pre-check: Collect existing files/directories in the destination
        existing_items = self.collect_existing_items_in_destination()
            
        # If any items already exist, print them and raise an error
        if existing_items:
            print("The following items already exist in the destination:")
            for existing_item in existing_items:
                print(existing_item)
            raise FileExistsError("Some items already exist in the destination. No files were copied.")
        
        # If no conflicts, proceed with copying
        for item in srcdir.iterdir():
            dest_item = destdir / item.name
            
            # Copy the item (directory or file)
            if item.is_dir():
                shutil.copytree(item, dest_item)
            else:
                shutil.copy2(item, dest_item)
             
 
    def collect_existing_items_in_destination(self): 
        # Pre-check: Collect existing files/directories in the destination
        existing_items = []
        for item in self._srcpath.iterdir():
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
    misslist = idm.get_missing_md5hashes_for_subdirs(src)
    for m in misslist:
        print(m)

    print("main(): all done")
    

if __name__ == "__main__":
    main()
   