from datetime import datetime
import hashlib
import os
from pathlib import Path
import time


class MD5Dir:

    MD5HASHES_FILENAME = ".md5_hashes.txt"

    def __init__(self):
        pass               

    def create_md5_from_string(self, data:str):
        md5 = hashlib.md5(data)
        return md5.hexdigest()                               

    @staticmethod
    def create_md5_from_file(file_path:Path, chunk_size=4096) -> str:
        """Calculate the MD5 hash of a file."""
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                md5.update(chunk)
        return md5.hexdigest()   
    
    """
        If the md5hashlist_file is not existing --> it will be created (empty file).
    """
    def get_dict_from_md5hashes_file(self, md5hashlist_filepath:Path):
        filelist = {}
        if md5hashlist_filepath.exists():                        
            with open(md5hashlist_filepath, "r", encoding='utf-8') as f:
                for line in f:
                    file_path, md5_hash_value = line.strip().split(": ")
                    filelist[file_path] = md5_hash_value
        return filelist  
    
    def get_missing_md5hashes_for_subdirs(self, rootdir:Path):
        # Traverse destination-tree and check if MD5-hashes exists in each directory in 
        # a file called '.md5_hashes.txt'. 
        # If it is not found, it will be created (if there are files in this folder)
        # If the file is found, the function checks, if all the hashes for all the files in the current 
        # folder are the '.md5_hashes.txt'. 
        # --> The ones which are missing are collected and given back in a list.
        missinglist = []
        for dir, _, files in os.walk(rootdir):
            dir_path = Path(dir)
            md5hashlist_filepath = dir_path / MD5Dir.MD5HASHES_FILENAME                
            filelist = {}
            if len(files) > 0:
                if not md5hashlist_filepath.exists():
                    # Create a new file:
                    with open(md5hashlist_filepath, 'w', encoding='utf-8') as _:
                        pass
                filelist = self.get_dict_from_md5hashes_file(md5hashlist_filepath)

            for curr_file in files:
                if curr_file != MD5Dir.MD5HASHES_FILENAME and curr_file not in filelist:
                    missinglist.append(dir_path / curr_file)
        return missinglist    
    
    def write_md5hashes_file(self, md5hashes_filename:Path, file_hashes:dict):
        if len(file_hashes) == 0: 
            return
        with open(md5hashes_filename, "w", encoding='utf-8') as f:
            for filename, file_hash in file_hashes.items():
                f.write(f"{filename}: {file_hash}\n")  

    def add_entry_to_md5hash_file(self, md5hashes_filename:Path, file_path:Path):
        file_hash = MD5Dir.create_md5_from_file(file_path)
        with open(md5hashes_filename, "a", encoding='utf-8') as f:
            f.write(f"{file_path.name}: {file_hash}\n")  
    
    def create_md5hashes_for_filelist(self, filelist:list) -> float:
        start_time = time.time()   
        for fp in filelist:
            filepath = Path(fp)
            if not filepath.exists():
                raise FileNotFoundError(f"File from filelist not found: {filepath}")

            parent_folder = filepath.parent
            md5hashes_filename = parent_folder / MD5Dir.MD5HASHES_FILENAME    
            self.add_entry_to_md5hash_file(md5hashes_filename, filepath)

        runtime = time.time() - start_time
        return runtime
    
    def create_md5hashes_for_tree(self, rootdir:Path, overwrite=False, only_one_dir=False) -> tuple:
        """
            Traverse the directory and subdirectories, creating '.md5_hashes.txt' 
            with key: value-painrs: filename: md5-hash.
            return: runtime in milliseconds
        """
        start_time = time.time()   
        totalbytes = 0  
        for dir, _, files in os.walk(rootdir):
            dir_path = Path(dir)
            file_hashes = {}
            for filename in files:
                if filename == MD5Dir.MD5HASHES_FILENAME:  #dont create checksum for it
                    continue
                file_path = dir_path / filename
                totalbytes = totalbytes + file_path.stat().st_size
                file_hashes[filename] = MD5Dir.create_md5_from_file(file_path)
            
            md5hashes_filename = dir_path / MD5Dir.MD5HASHES_FILENAME
            # if overwrite is false --> first check if the '.md5_hashes.txt' already exists:
            if overwrite == False and md5hashes_filename.exists():
                raise FileExistsError(f"md5hashes-filename already exists: {md5hashes_filename}")    
                
            self.write_md5hashes_file(md5hashes_filename, file_hashes)

            if only_one_dir: 
                break  # --> not walking down the tree ... finishing after the work on top-dir.

        runtime = time.time() - start_time
        return (runtime, totalbytes)
    
    def create_md5hashes_for_dir(self, dir_path:Path, overwrite=False) -> tuple:
        return self.create_md5hashes_for_tree(dir_path, overwrite, only_one_dir=True)
    
    def checksum_validation_for_dir(self, dir:Path) -> tuple:
        start_time = time.time() 
        md5hashes_filename = dir / MD5Dir.MD5HASHES_FILENAME 

        missmatches = {}
         # Load expected hashes from .md5_hashes.txt --> the file will be created if not found!
        expected_hashes = self.get_dict_from_md5hashes_file(md5hashes_filename)          
        
        # Check each file's MD5 against the expected value
        for file_name, expected_md5 in expected_hashes.items():
            file_path = dir / file_name
            if not file_path.exists():
                raise FileNotFoundError(f"File '{file_name}' listed in 'md5_hashes.txt' does not exist in the destination.")

            actual_md5 = MD5Dir.create_md5_from_file(file_path)
            if actual_md5 != expected_md5:
                missmatches[file_name] = (expected_md5, actual_md5)
                print(f"Checksum mismatch for file '{file_name}' in '{dir}': expected {expected_md5}, got {actual_md5}")
        runtime = time.time() - start_time
        return (runtime, missmatches)
    
    def checksum_validation_for_tree(self, rootdir: Path) -> tuple:
        start_time = time.time() 
          
        for curdir, dirs, files in os.walk(rootdir):
            md5hashes_filename = Path(curdir) / MD5Dir.MD5HASHES_FILENAME 
            missmatches = {}
            # Load expected hashes from .md5_hashes.txt --> the file will be created if not found!
            expected_hashes = self.get_dict_from_md5hashes_file(md5hashes_filename)    

            # Check each file's MD5 against the expected value
            for file_name, expected_md5 in expected_hashes.items():
                file_path = Path(curdir) / file_name
                if not file_path.exists():
                    raise FileNotFoundError(f"File '{file_name}' listed in 'md5_hashes.txt' does not exist in {curdir}")

                actual_md5 = MD5Dir.create_md5_from_file(file_path)
                if actual_md5 != expected_md5:
                    missmatches[file_name] = (expected_md5, actual_md5)
                    print(f"Checksum mismatch for file '{file_name}' in '{dir}': expected {expected_md5}, got {actual_md5}")
            # end for
        # end walk
        runtime = time.time() - start_time
        return (runtime, missmatches)                      

def main():
    print("main(): start ...")
    src = r"C:\tmp\testsrc"
    helper = MD5Dir()

    #runtime = helper.create_md5hashes_for_subdirs(src, overwrite=True)

    # misslist = helper.get_missing_md5hashes_for_subdirs(src)
    # print(f"Number of missing hashes: {len(misslist)}")
    # for m in misslist:
    #     print(m)
    # runtime = helper.create_md5hashes_for_filelist(misslist)

    # runtime, fails = helper.checksum_validation_for_dir(Path(src) / "unicode_validation")
    # print(f"Total checksum violations: {len(fails)}")
    # for f, hashes in fails.items():
    #     print(f"{str(f).ljust(40, '.')} old={hashes[0]}")
    #     print(f"{str(f).ljust(40, '.')} new={hashes[1]}")

    testpath = Path(r"D:\Games\Overwolf")
    # testpath = Path(r"D:\_privat\projekte\GUIFormExamples")
    runtime, bytes = helper.create_md5hashes_for_tree(testpath, overwrite=True)
    
    print(f"Runtime: --- {runtime:.3f} seconds.  Bytes={bytes}")  
    print("main(): all done")
    


if __name__ == "__main__":
    main()