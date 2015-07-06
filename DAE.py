"""
    This code is copied from a tutorial that introduces the multilayer perceptron using Theano,
    cf. http://deeplearning.net/tutorial/logreg.html.
    
    A Denoising-Auto-Encoder is a linear regressor where
    instead of feeding the input to the linear regression you insert a
    intermediate layer, called the hidden layer, that has a nonlinear
    activation function (usually tanh or sigmoid) . One can use many such
    hidden layers making the architecture deep. The application is to denoise
    input depending on time. No assumptions on the nature of the noise is made. If the noise 
    has a complicated structure, more internal layers might be necessary.
    
    .. math::
    
    f(x) = b^{(2)} + W^{(2)}( s( b^{(1)} + W^{(1)} x)),
    
    References:
    - websites: http://deeplearning.net
    - textbooks: "Pattern Recognition and Machine Learning" -
    Christopher M. Bishop, section 5
    
    """
__docformat__ = 'restructedtext en'


import os
import sys
import timeit

import math
import numpy as np

import theano as th
import theano.tensor as T

from linear_sgd import LinearRegression


# start-snippet-1
class HiddenLayer(object):
    def __init__(self, rng, input, n_in, n_out, W=None, b=None,
                 activation=T.nnet.sigmoid):
        """
            Typical hidden layer of a MLP: units are fully-connected and have
            sigmoidal activation function. Weight matrix W is of shape (n_in,n_out)
            and the bias vector b is of shape (n_out,).
            
            NOTE : The nonlinearity used here is sigmoid
            
            Hidden unit activation is given by: sigmoid(dot(input,W) + b)
            
            :type rng: numpy.random.RandomState
            :param rng: a random number generator used to initialize weights
            
            :type input: theano.tensor.dmatrix
            :param input: a symbolic tensor of shape (n_examples, n_in)
            
            :type n_in: int
            :param n_in: dimensionality of input
            
            :type n_out: int
            :param n_out: number of hidden units
            
            :type activation: theano.Op or function
            :param activation: Non linearity to be applied in the hidden
            layer
            """
        self.input=input
        self.activation=activation
        # end-snippet-1
        
        # `W` is initialized with `W_values` which is uniformely sampled
        # from sqrt(-6./(n_in+n_hidden)) and sqrt(6./(n_in+n_hidden))
        # for tanh activation function
        # the output of uniform if converted using asarray to dtype
        # theano.config.floatX so that the code is runable on GPU
        # Note : optimal initialization of weights is dependent on the
        #        activation function used (among other things).
        #        For example, results presented in [Xavier10] suggest that you
        #        should use 4 times larger initial weights for sigmoid
        #        compared to tanh
        #        We have no info for other function, so we use the same as
        #        tanh.
        if W is None:
            bound=np.sqrt(6. / (n_in+n_out))
            rngtmp=rng.uniform(low=-bound, high=bound, size=(n_in, n_out))
            W_values = np.asarray(rngtmp,dtype=th.config.floatX)
            if activation == T.nnet.sigmoid:
                W_values *= 4
                                     
        W = th.shared(value=W_values, name='W_hid', borrow=True)
        
        if b is None:
            b_values = np.zeros((n_out,), dtype=th.config.floatX)
            b = th.shared(value=b_values, name='b_hid', borrow=True)
                                         
        self.W = W
        self.b = b
                                         
        lin_output = T.dot(input, self.W) + self.b
        self.output = (
                       lin_output if self.activation is None
                       else self.activation(lin_output)
        )
        # parameters of the model
        self.params = [self.W, self.b]

    #transformation function
    def transform(self, input):
        lin_output = T.dot(input, self.W) + self.b
        self.output = (
                       lin_output if self.activation is None
                       else self.activation(lin_output)
                       )
        return self.output


# start-snippet-2
class DAE(object):
    """Denoising-Auto-Encoder Class
        
        A DAE is basically a multilayer perceptron which is a feedforward artificial neural network model
        that has one layer or more of hidden units and nonlinear activations.
        Intermediate layers usually have as activation function tanh or the
        sigmoid function (defined here by a ``HiddenLayer`` class)  while the
        top layer is a linear layer (defined here by a ``LinearRegression``
        class).
        """
    
    def __init__(self, rng, input, n_in, n_hidden):
        """Initialize the parameters for the multilayer perceptron
            
            :type rng: numpy.random.RandomState
            :param rng: a random number generator used to initialize weights
            
            :type n_in: int
            :param n_in: number of input units, the dimension of the space in
            which the datapoints lie
            
            :type n_hidden: int
            :param n_hidden: number of hidden units
            
            :type n_out: int
            :param n_out: number of output units, the dimension of the space in
            which the labels lie
            
            """
        #store size variables
        self.n_in=n_in
        self.n_hidden=n_hidden
        self.istrained=False
        # keep track of model input
        self.input=input
        
        # Since we are dealing with a one hidden layer MLP, this will translate
        # into a HiddenLayer with a sigmoid activation function connected to the
        # LinearRegression layer; the activation function can be replaced by
        # tanh or any other nonlinear function
        self.hiddenLayer = HiddenLayer(
                                       rng=rng,
                                       input=input,
                                       n_in=n_in,
                                       n_out=n_hidden,
                                       activation=T.nnet.sigmoid
        )
            
        # The linear regression layer gets as input the hidden units
        # of the hidden layer
        self.linRegressionLayer = LinearRegression(
                                                    input=self.hiddenLayer.output,
                                                    n_in=n_hidden,
                                                    n_out=n_in
        )
            
        # end-snippet-2 start-snippet-3
        # L1 norm ; one regularization option is to enforce L1 norm to
        # be small
        self.L1 = (
                   abs(self.hiddenLayer.W).sum() + abs(self.linRegressionLayer.W).sum()
        )
                                       
        # square of L2 norm ; one regularization option is to enforce
        # square of L2 norm to be small
        self.L2_sqr = (
                        (self.hiddenLayer.W ** 2).sum() + (self.linRegressionLayer.W ** 2).sum()
        )
                                       
        # negative log likelihood of the MLP is given by the negative
        # log likelihood of the output of the model, computed in the
        # linear regression layer
        self.negative_log_likelihood = (
                                        self.linRegressionLayer.negative_log_likelihood
        )
        # same holds for the function computing the number of errors
        self.errors = self.linRegressionLayer.errors
                                       
        # the parameters of the model are the parameters of the two layer it is
        # made out of
        self.params = self.hiddenLayer.params + self.linRegressionLayer.params
        # end-snippet-3
    
    
    
    #this is the actual denoising operation: return (W.h+b), where h is the result obtained by the hidden layer:
    def denoise(self,input):
        if not self.istrained:
            print 'You have to train the network first!'
            return None
        
        x=T.vector('x')
        predict=th.function(
                            inputs=[x],
                            outputs=self.linRegressionLayer.transform(self.hiddenLayer.transform(x))
        )
        return predict(input)



def train_DAE(train_set_x, train_set_y, valid_set_x, valid_set_y, learning_rate=0.01, L1_reg=0.00, L2_reg=0.0001, n_epochs=1000, batch_size=None, n_hidden=500):
    """
        Demonstrate stochastic gradient descent optimization for a multilayer
        perceptron
        
        :type train_set_x matrix:
        :param train_set_x: input training vectors stored as a matrix:
        the number of columns should be equal to the dimension of the problem and the number of rows is the number of total training samples
        
        :type train_set_y matrix:
        :param train_set_y: input training vectors stored as a matrix:
        the number of columns should be equal to the dimension of the problem and the number of rows is the number of total training samples
        
        :type valid_set_x matrix:
        :param valid_set_x: input validation vectors stored as matrix:
        the number of columns should be equal to the dimension of the problem and the number of rows is the number of total validation samples
        
        :type valid_set_y matrix:
        :param valid_set_y: input validation vectors stored as matrix:
        the number of columns should be equal to the dimension of the problem and the number of rows is the number of total validation samples
        
        :type learning_rate: float
        :param learning_rate: learning rate used (factor for the stochastic gradient)
        
        :type L1_reg: float
        :param L1_reg: L1-norm's weight when added to the cost (see regularization)
        
        :type L2_reg: float
        :param L2_reg: L2-norm's weight when added to the cost (see regularization)
        
        :type n_epochs: int
        :param n_epochs: maximal number of epochs to run the optimizer
        
        :type dataset: string
        :param dataset: the path of the MNIST dataset file from
        http://www.iro.umontreal.ca/~lisa/deep/data/mnist/mnist.pkl.gz
        
    """
    #select batch size
    num_times=train_set_x.get_value(borrow=True).shape[1]
    if not batch_size:
        batch_size=num_times
    
    # compute number of minibatches for training and validation
    n_train_batches = int(np.floor(num_times / batch_size))
    n_valid_batches = n_train_batches
        
    ######################
    # BUILD ACTUAL MODEL #
    ######################
    print 'building the model ...'
        
    # allocate symbolic variables for the data
    index = T.lscalar()  # index to an epoch
    batch = T.lscalar()  # index to a [mini]batch
    x = T.vector('x')  # the data is presented as vector
    y = T.vector('y')  # the  are presented as another vector
        
    #random number generator
    rng = np.random.RandomState(12345)
    
    # construct the MLP class
    dae = DAE(
              rng=rng,
              input=x,
              n_in=num_times,
              n_hidden=n_hidden
    )
    
    # start-snippet-4
    # the cost we minimize during training is the negative log likelihood of
    # the model plus the regularization terms (L1 and L2); cost is expressed
    # here symbolically
    cost = (
            dae.negative_log_likelihood(y) + L1_reg * dae.L1 + L2_reg * dae.L2_sqr
    )
    # end-snippet-4


    # compiling a Theano function that computes the mistakes that are made
    # by the model on a minibatch
    validate_model = th.function(
                                inputs=[index,batch],
                                outputs=dae.errors(y),
                                givens={
                                        x: valid_set_x[index, (batch * batch_size):((batch + 1) * batch_size)],
                                        y: valid_set_y[index, (batch * batch_size):((batch + 1) * batch_size)]
                                    },
                                 on_unused_input='warn'
    )
            
    # start-snippet-5
    # compute the gradient of cost with respect to theta (stored in params)
    # the resulting gradients will be stored in a list gparams
    gparams = [T.grad(cost, param) for param in dae.params]
                     
    # specify how to update the parameters of the model as a list of
    # (variable, update expression) pairs
    updates = [
                (param, param - learning_rate * gparam)
                for param, gparam in zip(dae.params, gparams)
                ]
                     
    # compiling a Theano function `train_model` that returns the cost, but
    # in the same time updates the parameter of the model based on the rules
    # defined in `updates`
    train_model = th.function(
                              inputs=[index,batch],
                              outputs=cost,
                              updates=updates,
                              givens={
                                        x: train_set_x[index, (batch * batch_size): ((batch + 1) * batch_size)],
                                        y: train_set_y[index, (batch * batch_size): ((batch + 1) * batch_size)]
                                        },
                              on_unused_input='warn'
    )
    # end-snippet-5
                     
    ###############
    # TRAIN MODEL #
    ###############
    print 'training ...'

    # early-stopping parameters
    patience = 10000  # look as this many examples regardless
    patience_increase = 2  # wait this much longer when a new best is found
    improvement_threshold = 0.995  # a relative improvement of this much is considered significant
    validation_frequency = min(n_train_batches, patience / 2)
    # go through this many
    # minibatche before checking the network
    # on the validation set; in this case we
    # check every epoch
                     
    best_validation_loss = np.inf
    best_iter = 0
    test_score = 0.
    start_time = timeit.default_timer()
        
    #initialize loop parameters
    epoch = 0
    done_looping = False
                     
    while (epoch < n_epochs) and (not done_looping):
        epoch = epoch + 1
            
        #minibatch iteration per epoch
        for minibatch_index in xrange(n_train_batches):
                                 
            minibatch_avg_cost = train_model(epoch-1,minibatch_index)
            # iteration number
            iter = (epoch - 1) * n_train_batches + minibatch_index
                                         
            if (iter + 1) % validation_frequency == 0:
                # compute zero-one loss on validation set
                validation_losses = [validate_model(epoch-1,i) for i in xrange(n_valid_batches)]
                this_validation_loss = np.mean(validation_losses)
                                                     
                print(
                      'epoch %i, minibatch %i/%i, validation error %f %%' %
                      (epoch, minibatch_index + 1, n_train_batches, this_validation_loss * 100.)
                )
                                                         
                # if we got the best validation score until now
                if this_validation_loss < best_validation_loss:
                    #improve patience if loss improvement is good enough
                    if (this_validation_loss < best_validation_loss * improvement_threshold):
                        patience = max(patience, iter * patience_increase)
                        best_validation_loss = this_validation_loss
                        best_iter = iter

                                                                                               
            if patience <= iter:
                done_looping = True
                break

        #DAE is trained
        dae.istrained=True

    #print stats
    end_time = timeit.default_timer()
    print(('Optimization complete. Best validation score of %f %% obtained at iteration %i %%') % (best_validation_loss * 100., best_iter + 1))
    print >> sys.stderr, ('The code for file ' +os.path.split(__file__)[1] +' ran for %.2fm' % ((end_time - start_time) / 60.))

    return dae

