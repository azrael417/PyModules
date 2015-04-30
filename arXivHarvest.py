from sickle import Sickle

class Harvester:
    sickle=None
    baseURL='http://export.arxiv.org/oai2'


    def __init__(self):
        self.sickle=Sickle(self.baseURL)


    def GetRecords(self,date=None,setname='physics:hep-lat'):
        dict={'metadataPrefix':'oai_dc', 'set':setname}
        if date:
            dict['from']=date
        return self.sickle.ListRecords(**dict)


    def GetRecordInfo(self,record):
        for event,elem in record:
            print event,elem
