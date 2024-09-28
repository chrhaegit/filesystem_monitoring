from pathlib import Path
import json 
import locale

class JsonConfig:
    def __init__(self, config_filename:str):
        self.__config_filename = Path.cwd() / "system" / config_filename
        self.__data = self.readjson_config()

    @property
    def config_filename(self):
        return self.__config_filename


    @property
    def data(self):
        return self.__data
    
    @data.setter
    def data(self, newdata:dict):
        self.__data = newdata

    def getvalue(self, key:str):
        return self.data[key]

    def readjson_config(self):        
        data = {}
        with open(self.config_filename, "r",  encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                pass
        return data

    def writejson(self):
        with open(self.config_filename, "w", encoding='utf-8') as f:
            json.dump(self.__data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def init_default_zone_s_config():
        zone_s_conf = JsonConfig("zone_s_config.json")
        conf = {"directories" : [r"C:\tmp\zone_s_A", r"D:\_privat\tmp\zone_s_B"]}
        zone_s_conf.data = conf
        zone_s_conf.writejson()

    @staticmethod
    def init_default_zone_w_config():
        zone_w_conf = JsonConfig("zone_w_config.json")
        conf = {"directories" : [r"*"]}
        zone_w_conf.data = conf
        zone_w_conf.writejson()        

  
def main():
    print(f"start main() ...")
    
    #JsonConfig.init_default_zone_s_config()
    #JsonConfig.init_default_zone_w_config()


    print(f"main() end!")

if __name__ == "__main__":
    main()
