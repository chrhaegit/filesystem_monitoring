import os
from pathlib import Path
import hashlib
import shutil
 


class IntegrityDataMover:

    def __init__(self, src:str, dest:str):
        self._hash_md5 = hashlib.md5()

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
    
    def checksum_validation(self):
        """
        Validates the MD5 checksum of each file in the destination directory against
        the values listed in 'md5_hashes.txt' in each directory.

        Args:
        - destdir (Path): The destination directory where the copied files reside.
        
        Raises:
        - ValueError: If the destination directory does not exist.
        - FileNotFoundError: If an 'md5_hashes.txt' file is missing in any subdirectory.
        - RuntimeError: If any file's checksum does not match the expected checksum.
        """
        
        # Traverse destination directory and check MD5 hashes
        for root, _, files in os.walk(self._destpath):
            root_path = Path(root)
            md5_file_path = root_path / "md5_hashes.txt"
            
            # Ensure md5_hashes.txt exists
            if not md5_file_path.exists():
                raise FileNotFoundError(f"Checksum file 'md5_hashes.txt' is missing in directory: {root}")
            
            # Load expected hashes from md5_hashes.txt
            expected_hashes = {}
            with open(md5_file_path, "r") as f:
                for line in f:
                    file_path, md5_hash_value = line.strip().split(": ")
                    expected_hashes[file_path] = md5_hash_value
            
            # Check each file's MD5 against the expected value
            for file_name, expected_md5 in expected_hashes.items():
                file_path = root_path / file_name
                if not file_path.exists():
                    raise FileNotFoundError(f"File '{file_name}' listed in 'md5_hashes.txt' does not exist in the destination.")

                actual_md5 = self.create_md5_from_file(file_path)
                if actual_md5 != expected_md5:
                    print(f"Checksum mismatch for file '{file_name}' in '{root}': expected {expected_md5}, got {actual_md5}")
        
        print("All checksum validation done.")    
        
   
    def create_md5_from_file(self, fname:Path):
        
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                self._hash_md5.update(chunk)
        return self._hash_md5.hexdigest()
    
    def write_file_hashes(self):
        """
            Traverse the directory and subdirectories, creating 'md5_hashes.txt' 
            with key: value-painrs: filename: md5-hash.
        """
        for root, _, files in os.walk(self._src):
            file_hashes = {}
            
            for filename in files:
                file_path = os.path.join(root, filename)
                file_hashes[filename] = self.create_md5_from_file(file_path)
            
            # Write to files.txt
            with open(os.path.join(root, "md5_hashes.txt"), "w") as f:
                for filename, file_hash in file_hashes.items():
                    f.write(f"{filename}: {file_hash}\n")    
        



def main():
    src = r"C:\tmp\testsrc"
    #src = "D:/_privat/projekte/python/filesystem_monitoring/testpfad"
    dest = r"D:\_privat\projekte\python\filesystem_monitoring\test_dest"
    idm = IntegrityDataMover(src, dest) 
    
    # idm.write_file_hashes()
    #idm.copy_tree()
    idm.checksum_validation()

    print("main(): all done")
    

if __name__ == "__main__":
    main()
   