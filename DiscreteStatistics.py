import numpy as np
import matplotlib.pyplot as plt
import random

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
        for key in datainit:
            if key not in self.data:
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


    def PlotHistogram(self,normalized=True):
        if not self.count:
            print 'The data container is empty: add entries first'
            return
        
        #extract data and sort according to key
        list=[]
        for key in self.data:
            list.append((key,self.data[key]))
        list.sort(key=lambda tup: tup[0])

        #convert to np array
        X = np.arange(len(self.data))
        Y = np.array([x[1] for x in list])

        if normalized:
            Y=np.true_divide(Y,float(self.count))
        
        #plot as histogram:
        plt.bar(X, Y, align='center', width=0.5)
        plt.xticks(X, [x[0] for x in list])
        ymax = max([x[1] for x in list]) + 1
        if normalized:
            ymax/=float(self.count)
        plt.ylim(0, ymax)
        plt.show()


    #get numsamples random variates from the stored PMF:
    def RandomSample(self,numsamples=1,sd=None):
        #extract data and sort according to key
        list=[]
        for key in self.data:
            list.append((key,self.data[key]))
        list.sort(key=lambda tup: tup[0])

        #convert to np array
        X = np.arange(len(self.data))
        Y = np.array([x[1] for x in list])

        #generate random numbers
        result=[]
        random.seed(sd)
        for n in range(0,numsamples):
            rand=random.random()
            
            tmp=0.
            for i in range(0,len(Y)):
                tmp+=Y[i]/float(self.count)
                if rand<=tmp:
                    result.append(list[i][0])
                    break

        return result
