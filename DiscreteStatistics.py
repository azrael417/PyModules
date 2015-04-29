class Pmf:
    data={}
    count=0
    
    def _AddDict(self,datainit):
        for key in datainit:
            if not isinstance(datainit[key],int):
                print 'Please make sure that all your values in the dict are actually numbers!'
                return
            
            if not datainit[key]>0:
                print 'Please make sure that all your values in the dict are larger than zero!'
                return
            
            if key not in self.data:
                self.data[key]=datainit[key]
            else:
                self.data[key]+=datainit[key]


    def _AddList(self,datainit):
        for x in datainit:
            if x not in self.data:
                self.data[key]=1
            else:
                self.data[key]+=1
                    
                    
    def __init__(self,datainit=None):
        self.AddData(datainit)


    def GetCount(self):
        newcount=0
        for key in self.data:
            newcount+=self.data[key]
        return newcount


    def AddData(self,datainit):
        if datainit:
        
            if isinstance(datainit,dict):
                self._AddDict(datainit)
            
            elif isinstance(datainit,list):
                self._AddList(datainit)
            
            self.count=self.GetCount()


    def GetProbability(self,value):
        if value in self.data:
            return float(self.data[value])/float(self.count)
        else:
            return 0.
