import numpy as np
import matplotlib as plt
import string
from sickle import Sickle
from bs4 import BeautifulSoup
import json
import requests
import pyorient as po

#************************************************************************************************************************
#************************************************************************************************************************
#****** Useful Helper Functions *****************************************************************************************
#************************************************************************************************************************
#************************************************************************************************************************

journallist=['JHEP','Phys.Rev','Science','PoS','Phys.Lett','Nature','J.Phys','Int.J.Mod','Nucl.Phys','Eur.Phys.J']

def GetPublicationString(stringlist,mode='eprint'):
    #search the string with the arxiv in it:
    for item in stringlist:
        if mode=='eprint':
            if 'arxiv' in item:
                return item
        else:
            if 'arxiv' not in item:
                for journal in journallist:
                    if journal in item:
                        return item
    return ''


def NormalizeEprintString(id):
    #split the string and access the references
    id=string.split(id,'/')
    if string.find(id[-1],'.')>=0:
        eprint=id[-1]
    else:
        eprint=id[-2]+'/'+id[-1]
    return eprint


def NormalizeAuthorList(authorlist):
    #split the name string at the ',':
    normlist=[]
    for author in authorlist:
        stringsplit=author.rsplit(',')
        normlist.append(stringsplit[0]+', '+stringsplit[1][1]+'.')
    return normlist


def NormalizeAbstractString(abstract):
    abstract=abstract.replace('\"u', 'ue').replace('\"a', 'ae').replace('\"o', 'oe').replace('$','').replace('\n',' ').replace('\\','').replace('\'','').strip()
    return abstract

#************************************************************************************************************************
#************************************************************************************************************************
#****** Harvester Class *************************************************************************************************
#************************************************************************************************************************
#************************************************************************************************************************


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


    #from a given set of records, determine the ones which are written by a given author. The format should be <name>, <first name>:
    def SelectRecordsAuthor(self,records,name):
        #split the string in first name and family name:
        if len(string.split(name,", "))!=2:
            print 'Please specify a name in the format <family name>, <first name>'
            return
        familyname=string.split(name,", ")[0]
        firstname=string.split(name," ")[1]
        
        result=[]
        for record in records:
            contains=False
            authors=record.metadata['creator']
            
            for author in authors:
                if string.find(author,familyname)>=0:
                    if string.find(author,firstname)>=0:
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
        id=GetPublicationString(record.metadata['identifier'],mode='eprint')
        req=requests.get(id)

        #split the string and access the references
        eprint=NormalizeEprintString(id)

        #get page containing references
        reflist='http://arxiv.org/'+mode+'/'+eprint
        r=requests.get(reflist)

        #scrape the references
        soup=BeautifulSoup(r.text)
        references=[]
        for ref in soup.find_all("a",title="Abstract"):
            references.append(string.split(ref.get_text(),":")[1])

        return references
