import hashlib
import os
from pathlib import Path
import time

class MD5Helper:

    MD5HASHES_FILENAME = ".md5_hashes.txt"

    def __init__(self):
        pass

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
    def get_all_from_md5hashes_file(self, md5hashlist_filepath:Path):
        filelist = {}
        if md5hashlist_filepath.exists():                        
            with open(md5hashlist_filepath, "r") as f:
                for line in f:
                    file_path, md5_hash_value = line.strip().split(": ")
                    filelist[file_path] = md5_hash_value
        return filelist  
    
    def get_missing_md5hashes_for_subdirs(self, rootdir:Path):
        # Traverse destination-tree and check if MD5-hashes exists in each directory as 
        # a file called md5_hashes.txt. The first one which is missing raises as FileNotFoundError.
        # If the file is found, check if all the hashes for all the files in the current folder are 
        # the file. The ones which are missing are collected and given back in a list.
        missinglist = []
        for dir, _, files in os.walk(rootdir):
            dir_path = Path(dir)
            md5hashlist_filepath = dir_path / MD5Helper.MD5HASHES_FILENAME    
            
            filelist = {}
            if len(files) > 0:
                if not md5hashlist_filepath.exists():
                    # Create a new file:
                    with open(md5hashlist_filepath, 'w') as _:
                        pass
                filelist = self.get_all_from_md5hashes_file(md5hashlist_filepath)

            for curr_file in files:
                if curr_file != MD5Helper.MD5HASHES_FILENAME and curr_file not in filelist:
                    missinglist.append(dir_path / curr_file)
        return missinglist    
    
    def write_md5hashes_file(self, md5hashes_filename:Path, file_hashes:dict):
        with open(md5hashes_filename, "w") as f:
            for filename, file_hash in file_hashes.items():
                f.write(f"{filename}: {file_hash}\n")  

    def add_entry_to_md5hash_file(self, md5hashes_filename:Path, file_path:Path):
        file_hash = self.create_md5_from_file(file_path)
        with open(md5hashes_filename, "a") as f:
            f.write(f"{file_path.name}: {file_hash}\n")  
    
    def create_md5hashes_for_filelist(self, filelist:list) -> float:
        start_time = time.time()   
        for fp in filelist:
            filepath = Path(fp)
            if not filepath.exists():
                raise FileNotFoundError(f"File from filelist not found: {filepath}")

            parent_folder = filepath.parent
            md5hashes_filename = parent_folder / MD5Helper.MD5HASHES_FILENAME    
            self.add_entry_to_md5hash_file(md5hashes_filename, filepath)

        runtime = time.time() - start_time
        return runtime
    
    def create_md5hashes_for_subdirs(self, rootdir:Path, overwrite=False) -> float:
        """
            Traverse the directory and subdirectories, creating '.md5_hashes.txt' 
            with key: value-painrs: filename: md5-hash.
            return: runtime in milliseconds
        """
        start_time = time.time()     
        for dir, _, files in os.walk(rootdir):
            dir_path = Path(dir)
            file_hashes = {}
            for filename in files:
                file_path = dir_path / filename
                file_hashes[filename] = self.create_md5_from_file(file_path)
            
            md5hashes_filename = dir_path / MD5Helper.MD5HASHES_FILENAME

            # if overwrite is false --> first check if the '.md5_hashes.txt' already exists:
            if overwrite == False and md5hashes_filename.exists():
                raise FileExistsError(f"md5hashes-filename already exists: {md5hashes_filename}")    
                
            self.write_md5hashes_file(md5hashes_filename, file_hashes)

        runtime = time.time() - start_time
        return runtime
    
    def checksum_validation_for_dir(self, dir:Path) -> tuple:
        start_time = time.time() 
        md5hashes_filename = dir / MD5Helper.MD5HASHES_FILENAME 

        missmatches = {}
         # Load expected hashes from .md5_hashes.txt --> the file will be created if not found!
        expected_hashes = self.get_all_from_md5hashes_file(md5hashes_filename)          
        
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

def main():
    print("main(): start ...")
    src = r"C:\tmp\testsrc"
    helper = MD5Helper()

    #runtime = helper.create_md5hashes_for_subdirs(src, overwrite=True)

    # misslist = helper.get_missing_md5hashes_for_subdirs(src)
    # print(f"Number of missing hashes: {len(misslist)}")
    # for m in misslist:
    #     print(m)
    # runtime = helper.create_md5hashes_for_filelist(misslist)
    runtime, fails = helper.checksum_validation_for_dir(Path(src) / "unicode_validation")
    print(f"Total checksum violations: {len(fails)}")
    for f, hashes in fails.items():
        print(f"{str(f).ljust(40, '.')} old={hashes[0]}")
        print(f"{str(f).ljust(40, '.')} new={hashes[1]}")
    
    print(f"Runtime: --- {runtime:.3f} seconds")  
    print("main(): all done")
    

if __name__ == "__main__":
    main()