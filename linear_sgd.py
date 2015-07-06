import theano as th
import theano.tensor as T
import numpy as np

class LinearRegression(object):
    """Linear Regression Class
        
        The linear regression is fully described by a weight matrix :math:`W`
        and bias vector :math:`b`,
        cf. http://deeplearning.net/tutorial/logreg.html#creating-a-logisticregression-class
        """
    
    def __init__(self, input, n_in, n_out):
        """ Initialize the parameters of the linear regression
            
            :type input: theano.tensor.TensorType
            :param input: symbolic variable that describes the input of the
            architecture (one minibatch)
            
            :type n_in: int
            :param n_in: number of input units, the dimension of the space in
            which the datapoints lie
            
            :type n_out: int
            :param n_out: number of output units, the dimension of the result space
            
            """
        # start-snippet-1
        # initialize with 0 the weights W as a matrix of shape (n_in, n_out)
        self.W = th.shared(
                               value=np.zeros(
                                                 (n_in, n_out),
                                                 dtype=th.config.floatX
                                                 ),
                               name='W_vis',
                               borrow=True
                               )
        # initialize the baises b as a vector of n_out 0s
        self.b = th.shared(
                                value=np.zeros(
                                                  (n_out,),
                                                  dtype=th.config.floatX
                                                ),
                                name='b_vis',
                                borrow=True
                               )
                               
        # symbolic expression for computing the regression vector
        # Where:
        # W is a matrix where column-k represent the regression values for input k
        # x is a matrix where row-j  represents input training sample-j
        # b is a vector
        self.p_y_given_x = T.dot(input, self.W) + self.b
            
        #prediction is just dot product
        self.y_pred = self.p_y_given_x
        # end-snippet-1
                               
        # parameters of the model
        self.params = [self.W, self.b]
                               
        # keep track of model input
        self.input = input
    
    
    #negative log_likelihood:
    def negative_log_likelihood(self, y):
        """Return the mean of the negative log-likelihood of the prediction
            of this model under a given target distribution.
            
            .. math::
            
            \frac{1}{|\mathcal{D}|} \mathcal{L} (\theta=\{W,b\}, \mathcal{D}) =
            \frac{1}{|\mathcal{D}|} \sum_{i=0}^{|\mathcal{D}|}
            \log(P(Y=y^{(i)}|x^{(i)}, W,b)) \\
            \ell (\theta=\{W,b\}, \mathcal{D})
            
            :type y: theano.tensor.TensorType
            :param x: vector containing input results
            :param y: vector containing true results to test against
            """
        # start-snippet-2
        # this is just the L2 norm of the fit minus y, i.e. chi^2/2, since p\sim exp(-\chi^2/2)
        # however, we use the mean instead of the sum so that the learning rate is not dependent on the size
        # of the input vector
        return 0.5*T.mean((self.y_pred-y) ** 2)
    # end-snippet-2
    
    #transform values
    def transform(self, input):
        #this is how the input is transformed
        self.p_y_given_x = T.dot(input, self.W) + self.b
        self.y_pred = self.p_y_given_x
        
        return self.y_pred
    
    
    #error:
    def errors(self, y):
        """Returns the error between the prediction and true values
            
            :type y: theano.tensor.TensorType
            :param y: the vector containing the true values to test against
            """
        
        # check if y has same dimension of y_pred
        if y.ndim != self.y_pred.ndim:
            raise TypeError(
                            'y should have the same shape as self.y_pred',
                            ('y', y.type, 'y_pred', self.y_pred.type)
                            )
        
        #return mean error value
        return 0.5*T.mean((self.y_pred-y) ** 2)

