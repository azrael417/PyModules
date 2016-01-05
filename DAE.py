import tensorflow as tf
import numpy as np

#useful definitions for weight and bias initialization
def weight_variable(shape,name):
    initial=tf.truncated_normal(shape,stddev=0.1)
    return tf.Variable(initial,name=name)

def bias_variable(shape,name):
    initial=tf.constant(0.1,shape=shape)
    return tf.Variable(initial,name=name)


class DAE(object):
    def __init__(self,input):
        #init everything
        self.sess=tf.Session()
        
        #safe input:
        self.input=input
        
        self.num_samples=input.shape[0]
        self.num_dimensions=input.shape[1]

        #define placeholders
        self.x=tf.placeholder("float", shape=[None,self.num_dimensions],name="input-vector")

        #dropout for reducing overfitting
        self.keep_prob_1=tf.placeholder("float",name="randint")
        with tf.name_scope("drop-1"):
            self.h_drop=tf.nn.dropout(self.x,self.keep_prob_1)

        #inner dimension size:
        self.num_inner_dimensions=int(np.floor(self.num_dimensions/4))

        #layer 1:
        #weights
        self.W_1=weight_variable([self.num_dimensions,self.num_inner_dimensions],name="weights-1")
        self.b_1=bias_variable([self.num_inner_dimensions],name="biases-1")
        #crossfire
        with tf.name_scope("sigmoid-1"):
            self.h_1=tf.nn.sigmoid(tf.matmul(self.h_drop,self.W_1)+self.b_1)
        
        #layer 2:
        #weights
        self.W_2=weight_variable([self.num_inner_dimensions,self.num_dimensions],name="weights-2")
        self.b_2=bias_variable([self.num_dimensions],name="biases-2")
        #crossfire
        with tf.name_scope("sigmoid-2"):
            self.h_2=tf.nn.sigmoid(tf.matmul(self.h_1,self.W_2)+self.b_2)
        
        #l2 difference
        with tf.name_scope("l2norm"):
            self.l2norm=tf.nn.l2_loss(tf.sub(self.x,self.h_2))

        #setting up the solver
        with tf.name_scope("train") as scope:
            self.train_step=tf.train.AdamOptimizer(1.e-4).minimize(self.l2norm)

        #init variables
        self.sess.run(tf.initialize_all_variables())


    def train(self, num_iters, batchsize, keep_prob=0.5):
        for i in range(num_iters):
            batch=self.input[i*batchsize:(i+1)*batchsize,:]

            if i%100==0:
                #feed dictionary
                feed={self.x:batch, self.keep_prob_1:1.}
                result=self.sess.run([self.l2norm],feed_dict=feed)
            
                #print accuracy
                print("step %d, training error %g"%(i,result[0]))
            else:
                #feed dictionary
                feed={self.x:batch, self.keep_prob_1:keep_prob}
