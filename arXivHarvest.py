from sickle import Sickle
import cElementTree as ET

class arXivHarvest:
    sickle=Null
    baseURL='http://export.arxiv.org/oai2'

    def __init__(self,setname='physics:hep-lat'):
        sickle=Sickle(baseURL)

    def GetRecords(self,setname='physics:hep-lat'):
        return sickle.ListRecords(metadataPrefix='oai_dc',set=setname)

    def GetValue(self,record,tag):
        dom = ET.parse(open(record, "r"))
        print dom