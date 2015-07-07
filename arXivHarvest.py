## @package arXivHarvest
# This module offers functions to extract metadata from arXiv using the Open Archives Initiative (OAI) metadata harvesting API.
# It can harvest publications, references and papers which cite papers of interest and store everything in a Graph DB.
# For that reason, the module needs an instance or OrientDB to be set up and running. It also harvests authors and tries to normalize
# journal names (unfortunately, the arXiv and Inspires databases do not do that necesarily).
#
# For more information on OAI visit http://www.openarchives.org/pmh/, and for more info how the python module sickle works,
# visit http://www.openarchives.org/pmh/.
#

import numpy as np
import matplotlib as plt
import string
from sickle import Sickle
from bs4 import BeautifulSoup
import json
import requests
import pyorient as po
import unicodedata
import editdistance as ed
from fuzzywuzzy import fuzz
import ads

## Helper functions
# This sections contains functions which are used by the harvester classed:

## class dummyrec:
# This will provide a dummy class which has the same access patter as a sickle record.
# It allows to unify parts of the code and reduces case handling significantly.
class dummyrec:
    
    ## __init__(self,dictionary)
    # The constructor takes a dictionary and creates a dummy record.
    def __init__(self,dictionary):
        self.metadata=dictionary

## journallist
# This is a list of journals I match the arxiv and Inspire entries against. It would be nice to scrape a list from the web
# but I was not successful of finding one so far.
journallist=set(['JHEP','Phys.Rev.Lett','Phys.Rev.C','Phys.Rev.D','Science','PoS LAT','PoS ICHEP','PoS HADRON','PoS KAON','PoS BEAUTY','PoS CONFINEMENT X','Phys.Lett.B','Phys.Lett.C','Nature','J.Phys','Int.J.Mod','Int.J.Mod.Phys.Conf.Ser.','Progr.Part.Nucl.Phys','Nucl.Phys.B','Nucl.Phys.A','Eur.Phys.J','Commun.Math.Phys','Phys.Rept','Annals Math','Annals Phys','Comput.Phys.Commun.','AIP Conf.Proc.','PTEP','Proc.Nat.Acad.Sci.','Few Body Syst.','Lect. Notes Phys.'])


## RemoveSymbols(string)
# converst string from unicode to ascii and removes all sorts of unwanted characters. Furthermore, it replaces the
# authorname "Duerr" by "Durr". At some point, I have to create a translate list of journals and authornames to
# simplify certain things and clean the code up.
def RemoveSymbols(string):
    string=unicodedata.normalize('NFKD', unicode(string)).encode('ascii', 'ignore').replace('Duerr','Durr').replace('\'','').strip()
    return string


## GetPublicationString(stringlist,mode='eprint')
# The Journal identifiers returned from the OAI harvester contain a list of records, usually containing the arXiv-id,
# the (unnormalized because it is entered by the author who submitted tha paper) Journal publications string (if available) as well
# as a Document Identitfier (doi). The arguments to this function is the list of identifiers and the mode is a flag which either tells
# the routine to return the arXiv id (mode='eprint', default) or journal name (mode!='eprint').
# The routine is lengthy because it has to do a lots of case handling.
def GetPublicationString(stringlist,mode='eprint'):
    #search the string with the arxiv in it:
    for item in stringlist:
        if mode=='eprint':
            if 'arxiv' in item or 'INSPIRE' in item:
                return item
        else:
            result=None
            if 'arxiv' not in item and 'INSPIRE' not in item:
                #if the item contains a doi: remove the doi stuff:
                if 'doi:' in item:
                    splititem=item.rsplit('/')
                    if len(splititem)>2:
                        item=splititem[1]
            
                #find first digit (if string contains digits) and remove averything fom there on:
                digitpos=[x.isdigit() for x in item]
                if np.any(digitpos):
                    index=digitpos.index(True)
                    itemnodigits=item[:index]
                else:
                    itemnodigits=item
        
                #strip off all digits and spaces and interpunction:
                all=string.maketrans('','')
                itemnodigits=item.translate(all,string.digits)
                itemnodigits=itemnodigits.strip().replace(',','').replace(':','').replace('.',' ').lower()
                
                #use fuzzy string matching
                maxmatch=0
                journ=''
                for journal in journallist:
                    
                    #condition journal string
                    journalshort=journal.strip().replace('.',' ').lower()
                    #compute fuzzy matching
                    fuzzmatch=fuzz.partial_ratio(journalshort,itemnodigits)
                    
                    #new distance is smaller than previous one:
                    if fuzzmatch>maxmatch:
                        journ=journal
                        maxmatch=fuzzmatch
            
                #if the matching is better than 50%, assume it is ok:
                info=RemoveSymbols(item)
                if maxmatch>50:
                    result=(journ,info)
                else:
                    result=('NA',info)
                return result

    #we could not determine a journal or eprint
    if mode=='eprint':
        return 'NA'
    else:
        return ('NA','NA')

## NormalizeEprintString(id):
# Tests if id is either from Inspire or arXiv. The former belong to incomplete Inspire entries and
# ca be treated as is. In case of the latter, we have to check if the new arXiv format is used (arXiv:YYMMDD.<four-digit-id>) or
# the old one (<subject-tag>/YYMMDD<id>).
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


def NormalizeAuthorList(client, authorlist):
    #split the name string at the ',':
    normlist=[]
    for author in authorlist:
        #first, check if Collaboration is contained in author:
        if 'ollaboration' in author:
            continue
        
        #this seems to be a real name
        authnorm=RemoveSymbols(author).replace('\u','ue')
        stringsplit=authnorm.rsplit(',')
        familyname=stringsplit[0].strip()
        if len(stringsplit)<2:
            firstname=''
        else:
            firstname=stringsplit[1].strip()
        
        #check if firstname is valid
        if len(firstname)<1:
            query=client.query("select from author where name like '%"+familyname+"%'", 1)
            if query:
                normlist.append(query[0].oRecordData['name'])
        else:
            normlist.append(familyname+', '+firstname[0]+'.')
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
    (journal,journalinfo)=GetPublicationString(record.metadata['identifier'],'journal')
    #eprint id
    arxivid=NormalizeEprintString(GetPublicationString(record.metadata['identifier'],'eprint'))
    #list of authors
    authors=NormalizeAuthorList(client,record.metadata['creator'])
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
        commandstring="create vertex publication set abstract='"+abstract+"', journal='"+journal+"', journalinfo='"+journalinfo+"', arxivid='"+arxivid+"', title='"+title+"', date='"+date+"'"
        client.command(commandstring)
    else:
        #query did return something, update the record
        commandstring="update publication set abstract='"+abstract+"', journal='"+journal+"', journalinfo='"+journalinfo+"', title='"+title+"', date='"+date+"' where arxivid='"+arxivid+"'"
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
    #def GetCitations(self,record,mode='refs'):
    #   id=GetPublicationString(record.metadata['identifier'],mode='eprint')
    #
    #    #split the string and access the references
    #    eprint=NormalizeEprintString(id)
    #
    #    #get page containing references
    #    reflist='http://arxiv.org/'+mode+'/'+eprint
    #    r=requests.get(reflist)
    #
    #    #scrape the references
    #    soup=BeautifulSoup(r.text)
    #
    #   #arxiv
    #   references=[]
    #   for ref in soup.find_all("a",title="Abstract"):
    #       references.append(string.split(ref.get_text(),":")[1])
    #
    #   #incomplete inspire
    #   for ref in soup.find_all("div","list-journal-ref"):
    #       text=ref.get_text()
    #       if 'Incomplete INSPIRE' in text:
    #           textsplit=string.split(text,"Journal-ref: ")[1]
    #           textsplit=RemoveSymbols(string.split(textsplit,"\n")[0].replace(',','_'))
    #           references.append("INSPIRE/"+textsplit)
    #
    #   return references
    
    
    
    #it is not a good idea to crawl arxiv, we should rather use the ADS service:
    def GetCitations(self,record,mode='refs'):
        id=GetPublicationString(record.metadata['identifier'],mode='eprint')
        
        #split the string and access the references
        eprint=NormalizeEprintString(id)
        
        #get the year:
        year=str.split(record.metadata['date'],"-")[0]
        
        #get page containing references
        reflist='http://adslabs.org/adsabs/abs/'+str(year)+'arXiv'+str(eprint)+'L/'
        r=requests.get(reflist)
    
        #scrape the references
        soup=BeautifulSoup(r.text)
    
        return soup
    
    

    def GetCiteRecord(self,citeid):
        if 'INSPIRE' not in citeid:
            #this is an arxiv reference, we can easily get that
            rec=self.sickle.GetRecord(**{'metadataPrefix':'oai_dc','identifier':'oai:arXiv.org:'+citeid})
        else:
            #journal
            publicationid=string.split(citeid,'INSPIRE/')[1]
            searchid=publicationid.replace('_',',')
            journal=RemoveSymbols(publicationid.replace('_',' '))
            eprint=RemoveSymbols(citeid)
            
            #this actually is an incomplete INSPIRE entry: we return a dictionary which contains all useful identifiers. The info we can get from spires itself using beautifulsoup:
            #the title can be obtained from the brief request
            #title
            req=requests.get("http://inspirehep.net/search?ln=de&ln=de&p=find+j+%22"+searchid+"%22&of=hb&action_search=Suchen&sf=earliestdate&so=d&rm=&rg=25&sc=0")
            soup=BeautifulSoup(req.text)
            
            #check if search yielded something reasonable
            if "Please try again." in soup.get_text():
                print 'Citation '+searchid+' cannot be found on INSPIRE! We will skip it'
                return None
            
            #else, get the title
            title=RemoveSymbols(soup.find_all("a","titlelink")[0].get_text())
            
            #for everything else, we need the detailed request
            req=requests.get("http://inspirehep.net/search?ln=de&ln=de&p=find+j+%22"+searchid+"%22&of=hd&action_search=Suchen&sf=earliestdate&so=d&rm=&rg=25&sc=0")
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
            rec=dummyrec({'title':[title], 'creator':creatorlist, 'description':['NA'], 'identifier':[eprint,journal], 'date':[date], 'subject':[subject]})

        return rec


    def UpdateJournalInspire(self,eprintid):
        #this actually is an incomplete INSPIRE entry: we return a dictionary which contains all useful identifiers. The info we can get from spires itself using beautifulsoup:
        #the title can be obtained from the brief request
        #title
        req=requests.get("http://inspirehep.net/search?ln=de&ln=de&p=find+eprint+%22"+eprintid+"%22&of=hb&action_search=Suchen&sf=earliestdate&so=d&rm=&rg=25&sc=0")
        soup=BeautifulSoup(req.text)
            
        #check if search yielded something reasonable
        if "Please try again." in soup.get_text():
            print 'Citation '+eprintid+' cannot be found on INSPIRE!'
            return ('NA','NA')
        
        linklist=soup.find_all("b")
        for link in linklist:
            linktext=link.get_text()
            if "| PDF" not in linktext:
                result=GetPublicationString([str(linktext)],mode='journal')
                return result

        return ('NA','NA')

#************************************************************************************************************************
#************************************************************************************************************************
#****** Functions using Harvester Class *********************************************************************************
#************************************************************************************************************************
#************************************************************************************************************************


