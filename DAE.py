import tensorflow as tf
import numpy as np

#useful definitions for weight and bias initialization using Xavier
def weight_variable(shape,name):
    wmax=4*np.sqrt(6./np.sum(shape))
    initial=tf.random_uniform(shape=shape,minval=-wmax,maxval=wmax)
    return tf.Variable(initial,name=name)

def bias_variable(shape,name):
    initial=tf.zeros_initializer(shape=shape)
    return tf.Variable(initial,name=name)


class DAE(object):
    def __init__(self,input,num_hidden):
        #init everything
        self.sess=tf.Session()
        
        #safe input:
        self.input=input
        
        #regularization:
        self.regularization=tf.placeholder("float",name="regularization")
        
        self.num_samples=input.shape[0]
        self.num_dimensions=input.shape[1]

        #define placeholders
        self.x=tf.placeholder("float", shape=[None,self.num_dimensions],name="input-vector")

        #dropout for reducing overfitting
        self.keep_prob_encoder=tf.placeholder("float",name="randint")
        with tf.name_scope("drop-encoder"):
            self.h_drop=tf.nn.dropout(self.x,self.keep_prob_encoder)
        
        #number of hidden units:
        self.num_hidden=num_hidden
        self.depth=(len(self.num_hidden)-1)*2
        
        #encoder:
        self.y=[]
        
        #weights
        self.W_encode=weight_variable([self.num_dimensions,self.num_hidden[0]],name="weights-encoder")
        print 'shape of weights-encoder: '+str(self.W_encode.get_shape())
        self.b_encode=bias_variable([self.num_hidden[0]],name="biases-encoder")
        #crossfire
        with tf.name_scope("sigmoid-encoder"):
            self.y.append(tf.nn.sigmoid(tf.matmul(self.h_drop,self.W_encode)+self.b_encode))
            print 'shape of y-encoded: '+str(self.y[0].get_shape())
        
        #hidden layers:
        self.W_hidden=[]
        self.b_hidden=[]
        for i in range(1,len(self.num_hidden)):
            #weights
            W_tmp=weight_variable([self.num_hidden[i-1],self.num_hidden[i]],name="weights-hidden-"+str(i))
            print 'shape of weights-hidden-'+str(i)+': '+str(W_tmp.get_shape())
            self.W_hidden.append(W_tmp)
            
            #biases
            b_tmp=bias_variable([self.num_hidden[i]],name="biases-hidden-"+str(i))
            self.b_hidden.append(b_tmp)
        
        #complete the stack by adding the transposed matrices to the weights:
        for i in range(1,len(self.num_hidden)):
            #weights
            W_tmp=tf.transpose(self.W_hidden[len(self.num_hidden)-i-1],name="weight-hidden-"+str(i-1+len(self.num_hidden)))
            print 'shape of weights-hidden-'+str(i-1+len(self.num_hidden))+': '+str(W_tmp.get_shape())
            self.W_hidden.append(W_tmp)
        
            #biases
            b_tmp=bias_variable([self.num_hidden[len(self.num_hidden)-i-1]],name="biases-hidden-"+str(i-1+len(self.num_hidden)))
            self.b_hidden.append(b_tmp)
        
        #compute the chain of outputs:
        for i in range(1,self.depth+1):
            with tf.name_scope("sigmoid-hidden-"+str(i)):
                self.y.append(tf.nn.sigmoid(tf.matmul(self.y[i-1],self.W_hidden[i-1])+self.b_hidden[i-1]))
                print 'shape of y-hidden-'+str(i)+': '+str(self.y[i].get_shape())
    
        #decoder:
        #weights
        self.W_decode=tf.transpose(self.W_encode,name="weights-decoder")
        print 'shape of weights-decode: '+str(self.W_decode.get_shape())
        self.b_decode=bias_variable([self.num_dimensions],name="biases-decoder")
        #crossfire
        with tf.name_scope("sigmoid-decoder"):
            self.z=tf.nn.sigmoid(tf.matmul(self.y[self.depth],self.W_decode)+self.b_decode)
        
        #l2 difference
        with tf.name_scope("l2norm"):
            self.l2norm=tf.nn.l2_loss(tf.sub(self.x,self.z))#+self.regularization*(2.*tf.nn.l2_loss(self.W)+tf.nn.l2_loss(self.b)+tf.nn.l2_loss(self.b_prime))

        #setting up the solver
        with tf.name_scope("train") as scope:
            self.train_step=tf.train.AdamOptimizer(1.e-4).minimize(self.l2norm)

        #init variables
        self.sess.run(tf.initialize_all_variables())


    def train(self, num_iters, batchsize, keep_prob=0.5, regularization=0.1):
        for i in range(num_iters):
            batch=self.input[i*batchsize:(i+1)*batchsize,:]

            if i%100==0:
                #feed dictionary
                feed={self.x:batch, self.keep_prob_encoder:1., self.regularization:regularization}
                result=self.sess.run([self.l2norm],feed_dict=feed)
            
                #print accuracy
                print("step %d, cost function %g"%(i,result[0]))
            else:
                #feed dictionary
                feed={self.x:batch, self.keep_prob_encoder:keep_prob, self.regularization:regularization}

    def transform(self, x):
        feed={self.x:[x], self.keep_prob_encoder:1., self.regularization: 0.}
        result=self.sess.run([self.z],feed_dict=feed)
        return result[0]

