
from jsonconfig import JsonConfig
from integrity_data_mover import IntegrityDataMover
from md5helper import MD5Helper


class FilesystemMonitoring:
    def __init__(self):
        self.__zone_s_conf = JsonConfig("zone_s_config.json")
        self.__zone_w_conf = JsonConfig("zone_w_config.json")
        self.__zone_transfers_conf = JsonConfig("zone_transfers_config.json")
            
    @property
    def zone_s_list(self):
        return self.__zone_s_conf.getvalue("directories")
    
    @property
    def zone_w_list(self):
        return self.__zone_w_conf.getvalue("directories")
    
    @property
    def zone_transfers_list(self):
        return self.__zone_transfers_conf.getvalue("transfers")
    
    def run(self):
        # 1. go through the zone-transfer-list and move whats required there
        try:
            self.zone_transfers_runner()
        except FileExistsError as fe:
            print(f"run(): zone_transfers_runner->aborted! {fe}")
        

        # 2. directory-structure monintoring

        # 3. checksum-monitoring
    
        
    def zone_transfers_runner(self):
        for transfer in self.zone_transfers_list:
            print(f"    src={transfer["source"]}    dst={transfer["destination"]}") 
            idm = IntegrityDataMover(transfer["source"], transfer["destination"]) 
            self.transfer_source_to_destination(idm)

    def transfer_source_to_destination(self, idm:IntegrityDataMover):        
        # Pre-check: Collect existing files/directories in the destination
        existing_items = idm.collect_existing_items_in_destination()
        # If any items already exist, print them and report/abort afterwards
        if existing_items:
            print("The following items already exist in the destination:")
            for item in existing_items:
                print(item)
            raise FileExistsError("Some items already exist in the destination. No files were copied.")            
        # else: create md5 hashes in sourcepath
        md5helper = MD5Helper()
        runtime, totalbytes = md5helper.create_md5hashes_for_tree(idm.sourcepath, overwrite=True)
        print(f"created md5-hashes in source: {idm.sourcepath} in {runtime:.3f} seconds for a total of {totalbytes:,} bytes")

        idm.copy_tree()
        #evaluate the checksums after the copy:
        runtime, fails = md5helper.checksum_validation_for_tree(idm.destpath)
        print(f"Total runtime for checksum_validation in destination after copy: {runtime}")
        if len(fails) > 0:
            print(f"Total checksum violations: {len(fails)}")
            for f, hashes in fails.items():
                print(f"{str(f).ljust(40, '.')} old={hashes[0]}")
                print(f"{str(f).ljust(40, '.')} new={hashes[1]}")
            # TODO: The question is what to do here.. just report or report and abort?

        #if the checksums are ok after copy_tree --> delete source-data
        idm.remove_source_content_only()

    def print_config(self):
        print(f"Zone S directories:")
        for z in self.zone_s_list:
            print(f"    {z}")
        
        print(f"Zone w directories:")
        for z in self.zone_w_list:
            print(f"    {z}")

        print(f"Zone-Transfer jobs:")
        for t in self.zone_transfers_list:
            print(f"    src={t["source"]}")     
            print(f"    dst={t["destination"]}\n")   

def main():
    print(f"start main() ...")
    fsmonitor = FilesystemMonitoring()
    #fsmonitor.print_config()
    fsmonitor.run()

        

    print(f"main() end!")

if __name__ == "__main__":
    main()
