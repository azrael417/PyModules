import numpy as np
import h5py

#start dense_to_one_hot
def dense_to_one_hot(labels_dense, num_classes=2):
    """Convert class labels from scalars to one-hot vectors."""
    num_labels = labels_dense.shape[0]
    index_offset = np.arange(num_labels) * num_classes
    labels_one_hot = np.zeros((num_labels, num_classes))
    labels_one_hot.flat[index_offset + labels_dense.ravel()] = 1
    return labels_one_hot
#end dense_to_one_hot


#start DataSet
class HDF5DataSet(object):
    
    #constructor
    def __init__(self, filepath, convert_to_one_hot=True, in_memory=False):
        
        #important variables
        self._filepath=filepath
        self._imagebase='image_'
        self._labelbase='label_'
        self._convert_to_one_hot=convert_to_one_hot
        
        #open file
        if in_memory:
            self._fi = h5py.File(self._filepath,'r',driver='core', **{backing_store:False})
        else:
            self._fi = h5py.File(self._filepath,'r')
        
        self._num_examples=self._fi['num_entries'][0]
        
        #compute dimension of input vector:
        shape=np.asarray(self._fi[self._imagebase+'0'].value).shape
        self._num_dimensions=np.prod(shape).astype(int)
        
        #set mean to zero
        self._data_mean=np.zeros(self._num_dimensions)
        
        #create vector of tags:
        self._tags=range(0,self._num_examples)
        
        #set epoch label and index in epoch
        self._epochs_completed = 0
        self._index_in_epoch = 0
    
    #destructor:
    def __del__(self):
        if self._fi:
            self._fi.close()
        self._epochs_completed = 0
        self._index_in_epoch = 0
    
    @property
    def num_examples(self):
        return self._num_examples
    
    @property
    def epochs_completed(self):
        return self._epochs_completed
    
    @property
    def num_dimensions(self):
        return self._num_dimensions
    
    def compute_mean(self):
        self._data_mean=np.zeros(self._num_dimensions)
        #load data and compute image mean
        for idx in range(self._num_examples):
            image=self._fi[self._imagebase+str(idx)].value
            image=np.reshape(image,self._num_dimensions)
            image=np.multiply(image,1.0 / (255.0*float(self._num_examples)))
            self._data_mean+=image
    
    def reset_mean(self):
        self._data_mean=np.zeros(self._num_dimensions)
    
    def next_batch(self, batch_size):
        """Return the next `batch_size` examples from this data set."""
        start = self._index_in_epoch
        self._index_in_epoch += batch_size
        if self._index_in_epoch > self._num_examples:
            # Finished epoch
            self._epochs_completed += 1
            print 'Epoch completed. Epochs completed: '+str(self._epochs_completed)
            # Shuffle the data
            np.random.shuffle(self._tags)
            # Start next epoch
            start = 0
            self._index_in_epoch = batch_size
            assert batch_size <= self._num_examples
        
        end = self._index_in_epoch
        
        #load the batch:
        images=[]
        labels=[]
        for idx in self._tags[start:end]:
            imarray=self._fi[self._imagebase+str(idx)].value
            images.append(imarray)
            label=(self._fi[self._labelbase+str(idx)].value)[0]
            labels.append(label)
        
        #reshape image vector and rescale
        images=np.asarray(images)
        images = images.reshape(images.shape[0],images.shape[1] * images.shape[2])
        # Convert from [0, 255] -> [0.0, 1.0].
        images = images.astype(np.float32)
        images = np.multiply(images, 1.0 / 255.0)
        
        #apply one-hot encoding to the labels:
        #convert to numpy arrays:
        labels=np.asarray(labels,dtype=np.uint8)
        if self._convert_to_one_hot:
            labels=dense_to_one_hot(labels)
        
        return images, labels
    
    def get_data(self):
        images=[]
        labels=[]
        for idx in range(self._num_examples):
            imarray=self._fi[self._imagebase+str(idx)].value
            images.append(imarray)
            label=(self._fi[self._labelbase+str(idx)].value)[0]
            labels.append(label)
        
        #reshape image vector and rescale
        images=np.asarray(images)
        images = images.reshape(images.shape[0],images.shape[1] * images.shape[2])
        # Convert from [0, 255] -> [0.0, 1.0].
        images = images.astype(np.float32)
        images = np.multiply(images, 1.0 / 255.0)
        #subtract mean
        images=np.subtract(images,self._data_mean,axis=1)

        #convert to numpy arrays:
        labels=np.asarray(labels,dtype=np.uint8)
        if self._convert_to_one_hot:
            labels=dense_to_one_hot(labels)
        
        return images, labels
#end HDF5DataSet


class DataSet(object):
    def __init__(self,data):
        self._num_examples=data.shape[0]
        self._num_dimensions=data.shape[1]
        self._data=data
        self._epochs_completed = 0
        self._index_in_epoch = 0
    @property
    def num_examples(self):
        return self._num_examples
    @property
    def num_dimensions(self):
        return self._num_dimensions
    def next_batch(self, batch_size):
        """Return the next `batch_size` examples from this data set."""
        start = self._index_in_epoch
        self._index_in_epoch += batch_size
        if self._index_in_epoch > self._num_examples:
            # Finished epoch
            self._epochs_completed += 1
            # Shuffle the data
            np.random.shuffle(self._data)
            # Start next epoch
            start = 0
            self._index_in_epoch = batch_size
            assert batch_size <= self._num_examples
        
        end = self._index_in_epoch
        return self._data[start:end]
