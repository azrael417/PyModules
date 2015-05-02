import string
from sickle import Sickle
from bs4 import BeautifulSoup
import json
import requests

class Harvester:
    sickle=None
    baseURL='http://export.arxiv.org/oai2'


    def __init__(self):
        self.sickle=Sickle(self.baseURL)


    def GetRecords(self,date1=None,date2=None,setname='physics:hep-lat'):
        dict={'metadataPrefix':'oai_dc', 'set':setname}
        if date1:
            dict['from']=date1
        if date2:
            dict['until']=date2
        return self.sickle.ListRecords(**dict)


    #from a given set of records, determine the ones which are written by a given author:
    def SelectRecordsAuthor(self,records,name):
        result=[]
        for record in records:
            contains=False
            for event,elem in record:
                if event=='creator':
                    authors=elem
                    break
            for author in authors:
                if string.find(author,name)>=0:
                    contains=True
                    break
            if contains:
                result.append(record)
        return result


    def PrintRecordInfo(self,record):
        for event,elem in record:
            print elem


    #get the papers which are cited (mode='refs') or the papers which cite the record (mode='cits')
    def GetCitations(self,record,mode='refs'):
        for event,elem in record:
            if event=='identifier':
                id=elem[0]
                break
        req=requests.get(id)

        #split the string and access the references
        id=string.split(id,'/')
        if string.find(id[-1],'.')>=0:
            eprint=id[-1]
        else:
            eprint=id[-2]+'/'+id[-1]

        #get page containing references
        reflist='http://arxiv.org/'+mode+'/'+eprint
        r=requests.get(reflist)

        #scrape the references
        soup=BeautifulSoup(r.text)
        references=[]
        for ref in soup.find_all("a",title="Abstract"):
            references.append(string.split(ref.get_text(),":")[1])

        return references




