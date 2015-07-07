## @package Bootstrap
# This module file provides routines for bootstrap resampling. The data should be stored in a 2D numpy array, where the different entries are
# stored in rows and the different values belonging to that entry in columns (similar to an SQL table)
# A seed for the internal rng can be passed to the routine.

## prerequesites
import numpy as np

# inmat is the num-measurements times num-variables matrix, numsamples is the number of bootstrap samples and a seed can be passed
# to override the internal default seed. The routine only does an atomic bootstrap (blocksize=1) at the moment, but will be extended sooner or later.
# The output is num-saples+1 times num-variables numpy array, where the 0th row contains the average over all input samples (equivalent with a bootstrap)
# where every entry is chosen exactly once
def Bootstrap(inmat,numsamples,axis=0,seed=104729):
    #initialize rng
    rng=np.random.RandomState(seed)
    
    if axis==1:
        inmat=np.transpose(inmat)
    resultmat=np.zeros((numsamples+1,inmat.shape[1]),dtype=inmat.dtype)
    inputsize=inmat.shape[0]
    
    #create output matrix
    resultmat[0,:]=np.mean(inmat,0)
    for s in range(0,numsamples):
        bset=rng.randint(0,inputsize,inputsize)
        resultmat[s+1,:]=np.mean(inmat[bset,:],0)
    
    #undo transposition
    if axis==1:
        inmat=np.transpose(inmat)
        resultmat=np.transpose(resultmat)
    return resultmat
