import numpy as np
import matplotlib as plt
import string
from sickle import Sickle
from bs4 import BeautifulSoup
import json
import requests
import pyorient as po
import unicodedata

#************************************************************************************************************************
#************************************************************************************************************************
#****** Useful Helper Functions *****************************************************************************************
#************************************************************************************************************************
#************************************************************************************************************************

journallist=set(['JHEP','Phys.Rev','Science','PoS','Phys.Lett','Nature','J.Phys','Int.J.Mod','Nucl.Phys','Eur.Phys.J','Commun.Math.Phys'])

def GetPublicationString(stringlist,mode='eprint'):
    #search the string with the arxiv in it:
    for item in stringlist:
        if mode=='eprint':
            if 'arxiv' in item or 'INSPIRE' in item:
                return item
        else:
            if 'arxiv' not in item and 'INSPIRE' not in item:
                for journal in journallist:
                    if journal in item:
                        return item
    return ''


def NormalizeEprintString(id):
    #incomplete inspire entries are treated as is:
    if 'INSPIRE' in id:
        return id
    
    #split the string and access the references
    id=string.split(id,'/')
    if string.find(id[-1],'.')>=0:
        eprint=id[-1]
    else:
        eprint=id[-2]+'/'+id[-1]
    return eprint


def RemoveSymbols(string):
    string=unicodedata.normalize('NFKD', unicode(string)).encode('ascii', 'ignore').replace('Duerr','Durr').replace('\'','').strip()
    return string

def NormalizeAuthorList(authorlist):
    #split the name string at the ',':
    normlist=[]
    for author in authorlist:
        authnorm=RemoveSymbols(author)
        stringsplit=authnorm.rsplit(',')
        if len(stringsplit)<2:
            continue
        familyname=stringsplit[0]
        firstname=stringsplit[1]
        normlist.append(familyname+', '+firstname[1]+'.')
    return normlist


def NormalizeAbstractString(abstract):
    abstract=abstract.replace('\"u', 'ue').replace('\"a', 'ae').replace('\"o', 'oe').replace('$','').replace('\n',' ').replace('\\','').replace('\'','').strip()
    return abstract


#put author into db
def SaveAuthorToDB(client,author):
    #check if author is already in db
    query=client.query("select from author where name='"+author+"'", 1)
    if not query:
        print 'Adding author '+author+' to the DB'
        #query did not return anything, add to db
        client.command("create vertex author set name='"+author+"'")
    else:
        print 'Author '+author+' is already in the DB'
    return


#put record into db:
def SaveRecordToDB(client,record):
    #abstract
    abstract=NormalizeAbstractString(record.metadata['description'][0])
    #journal
    journal=GetPublicationString(record.metadata['identifier'],'journal')
    #eprint id
    arxivid=NormalizeEprintString(GetPublicationString(record.metadata['identifier'],'eprint'))
    #list of authors
    authors=NormalizeAuthorList(record.metadata['creator'])
    #title
    title=NormalizeAbstractString(record.metadata['title'][0])
    #date
    date=record.metadata['date'][0]
    #subject
    subjects=record.metadata['subject']
    
    #create DB entry for subjects if not created yet
    for subject in subjects:
        query=client.query("select from subject where name='"+subject+"'", 1)
        if not query:
            print 'New subject '+subject+' found. Enter into DB.'
            commandstring="create vertex subject set name='"+subject+"'"
            client.command(commandstring)
        else:
            print 'Subject '+subject+' already in DB!'

    #create DB entry
    #check if publication is already in db
    query=client.query("select from publication where arxivid='"+arxivid+"'", 1)
    if not query:
        #query did not return anything, add to db
        commandstring="create vertex publication set abstract='"+abstract+"', journal='"+journal+"', arxivid='"+arxivid+"', title='"+title+"', date='"+date+"'"
        client.command(commandstring)
    else:
        #query did return something, update the record
        commandstring="update publication set abstract='"+abstract+"', journal='"+journal+"', title='"+title+"', date='"+date+"' where arxivid='"+arxivid+"'"
        client.command(commandstring)
    
    #test if edges between publication and subjects exist:
    for subject in subjects:
        #test if there is a connection from the subject to the publication
        commandstring="select from (select expand(out('belongstosubject').name) from publication where arxivid='"+arxivid+"') where value='"+subject+"'"
        query=client.command(commandstring)
    
        if not query:
            #edge does not exist. Create it
            commandstring="create edge belongstosubject from (select from publication where arxivid = '"+arxivid+"') to (select from subject where name = '"+subject+"')"
            client.command(commandstring)
        else:
            print 'Publication '+arxivid+' already linked to subject '+subject+'!'

    return


#link an author to a publication
def LinkAuthorToPublication(client,author,publicationid):
    #check if author is already in db and linked to publication
    query=client.query("select from author where name='"+author+"'", 1)
    if query:
        #author is in db, now test if there is an edge between the author and the paper:
        commandstring="select from (select expand(out('isauthorof').arxivid) from author where name='"+author+"') where value='"+publicationid+"'"
        query=client.command(commandstring)
            
        if not query:
            #edge does not exist. Create it
            commandstring="create edge isauthorof from (select from author where name = '"+author+"') to (select from publication where arxivid = '"+publicationid+"')"
            client.command(commandstring)
        else:
            print 'Author '+author+' already linked to id '+publicationid+'!'

    else:
        print 'Author '+author+' not found in DB!'
    return


#cite publication recA->recB on edge with name edgename
def CreateCitationLink(client,recA,recB):
    if recA==recB:
        print 'Both records are the same, abort.'
        return

    #get the eprint-ids
    arxividA=NormalizeEprintString(GetPublicationString(recA.metadata['identifier'],'eprint'))
    arxividB=NormalizeEprintString(GetPublicationString(recB.metadata['identifier'],'eprint'))

    #check if both publications are in the DB:
    query=client.query("select from publication where arxivid='"+arxividA+"'", 1)
    if not query:
        print 'Record id '+arxividA+' is not stored in the DB!'
        return
    query=client.query("select from publication where arxivid='"+arxividB+"'", 1)
    if not query:
        print 'Record id '+arxividB+' is not stored in the DB!'
        return

    #check if edge already exists:
    commandstring="select from (select expand(out('cites').arxivid) from publication where arxivid='"+arxividA+"') where value='"+arxividB+"'"
    query=client.command(commandstring)
    if not query:
        #edge does not exist. Create it
        commandstring="create edge cites from (select from publication where arxivid = '"+arxividA+"') to (select from publication where arxivid = '"+arxividB+"')"
        client.command(commandstring)
        print 'Linking record id '+arxividA+' to id '+arxividB+' using edge cites!'
    else:
        print 'Record id '+arxividA+' is already linked to id '+arxividB+' by edge cites!'
    return


#************************************************************************************************************************
#************************************************************************************************************************
#****** Harvester Class *************************************************************************************************
#************************************************************************************************************************
#************************************************************************************************************************
#dummy record, used for incomplete inspire entries:
class dummyrec:
    
    def __init__(self,dictionary):
        self.metadata=dictionary


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

    #print records
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
        
        #arxiv
        for ref in soup.find_all("a",title="Abstract"):
            references.append(string.split(ref.get_text(),":")[1])
        
        #incomplete inspire
        for ref in soup.find_all("div","list-journal-ref"):
            text=ref.get_text()
            if 'Incomplete INSPIRE' in text:
                textsplit=string.split(text,"Journal-ref: ")[1]
                textsplit=string.split(textsplit,"\n")[0].replace(',',' ')
                references.append("INSPIRE/"+textsplit)

        return references


    def GetCiteRecord(self,citeid):
        if 'INSPIRE' not in citeid:
            #this is an arxiv reference, we can easily get that
            rec=self.sickle.GetRecord(**{'metadataPrefix':'oai_dc','identifier':'oai:arXiv.org:'+citeid})
        else:
            #journal
            journal=string.split(citeid,'INSPIRE/')[1]
            
            #this actually is an incomplete INSPIRE entry: we return a dictionary which contains all useful identifiers. The info we can get from spires itself using beautifulsoup:
            #the title can be obtained from the brief request
            #title
            req=requests.get("http://inspirehep.net/search?ln=de&ln=de&p=find+j+%22"+journal+"%22&of=hb&action_search=Suchen&sf=earliestdate&so=d&rm=&rg=25&sc=0")
            soup=BeautifulSoup(req.text)
            title=RemoveSymbols(soup.find_all("a","titlelink")[0].get_text())
            
            #for everything else, we need the detailed request
            req=requests.get("http://inspirehep.net/search?ln=de&ln=de&p=find+j+%22"+journal+"%22&of=hd&action_search=Suchen&sf=earliestdate&so=d&rm=&rg=25&sc=0")
            soup=BeautifulSoup(req.text)
            

            #authors
            creatorlist=[]
            for r in soup.find_all("a","authorlink"):
                creatorlist.append(string.split(r.get_text()," ")[-1]+', '+string.split(r.get_text()," ")[0][0]+'.')
            
            #date
            datestring=RemoveSymbols(soup.find("div","recordlastmodifiedbox").get_text())
            datestring=string.split(datestring,"added ")[1]
            if "last modified" in datestring:
                datestring=string.split(datestring," last modified")[0]
            date=datestring.replace(',','').strip()
            
            #subject, set it to constant value for now:
            subject='INSPIRE Incomplete'

            #create dummy record
            rec=dummyrec({'title':[title], 'creator':creatorlist, 'description':['NA'], 'identifier':[citeid,journal], 'date':[date], 'subject':[subject]})

        return rec


#************************************************************************************************************************
#************************************************************************************************************************
#****** Functions using Harvester Class *********************************************************************************
#************************************************************************************************************************
#************************************************************************************************************************


