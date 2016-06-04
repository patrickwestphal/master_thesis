'''
Created on Jun 2, 2016

@author: Ivan Ivanov
'''

from sklearn.base import BaseEstimator, ClassifierMixin
from datasketch import MinHash, MinHashLSH
from scipy.sparse import csr_matrix
import numpy as np

class MinHashNearestNeighbor(BaseEstimator, ClassifierMixin):
    '''
    A radius-based approximate nearest neighbor classifier using the min-hashing heuristic.
    
    Info:
        sklearn API: http://scikit-learn.org/stable/developers/contributing.html
        min-hashing implementation: https://github.com/ekzhu/datasketch
    '''
    def __init__(self, w, k, threshold=None, L=None, label_majority_threshold=0.5, verbose=False):
        '''
        Initialization of the MHNN classifier.
        
        Parameters:
            w - Size of the sliding window for extracting w-shingles.
            k - Number of permutations (hash functions).
            threshold - (optional, default=None) Jaccard similarity
                        threshold. Can be calculated using `k` and `L`.
            L - (optional, default=None) Number of bands. Can be
                calculated using `k` and `threshold`.
            label_majority_threshold - (optional, default=0.5) A threshold
                                       defining the proportion of examples that
                                       need to have a particular label so that
                                       this label will be considered a majority
                                       label.
            verbose - (optional, default=False) Enable verbose output.
        '''
        if (threshold and L) or (not threshold and not L):
            raise ValueError("Only `threshold` or only `L` must be provided.")
        
        self.w = w
        self.k = k
        self.label_majority_threshold = label_majority_threshold
        self.verbose = verbose
        
        if L:
            self.L = L
            self.threshold = MinHashNearestNeighbor.get_threshold(self.k, self.L)
        else:
            self.threshold = threshold
            self.L = MinHashNearestNeighbor.get_L(self.k, self.threshold)
        
        self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.k)
    
#     # TODO: this implements fit for sparse matrix data. Not sure if it is useful.
#     def fit(self, X, y):
#         '''
#         Fit the model by creating a min-hashing sketch of the input data.
#         Parameters:
#             X - A (SciPy) CSR sparse binary matrix where each row represents a record
#                 and each column represents an attribute of a record. If X[i, j] = 1
#                 then record i has attribute j.
#             y - A binary matrix representing the labels of each record. Rows represent
#                 the same records as for X. Columns define class labels. If y[i, l] = 1
#                 then record i has label l. Each record may have multiple labels.
#         '''
#         if type(X) is not csr_matrix:
#             raise ValueError("`X` must be a binary matrix of type scipy.sparse.csr_matrix.")
#         if type(y) is not np.ndarray:
#             raise ValueError("`y` must be a binary matrix of type numpy.ndarray.")
#         if X.get_shape()[0] != np.shape(y)[0]:
#             raise ValueError("Inconsistent number of rows in `X` and `y`. They must be the same.")
#         
#         self.y = y
#         train_examples_count = np.shape(X)[0]
#         
#         for i in range(train_examples_count):
#             min_hash_i = MinHash(num_perm=self.k)
#             # get non-zero column indices (attributes) of row i
#             X_i_attributes = X[i].nonzero()[1]
#             for j in X_i_attributes:
#                 # TODO: not sure if this update will give good results since I already have the fingerprints
#                 min_hash_i.update(j)
#             self.lsh.insert(i, min_hash_i)
    
    def fit(self, X, y):
        '''
        Fit the model by creating a min-hashing sketch of the input data.
        Parameters:
            X - A list of strings. Each element defines one training example
                identified by its list index.
            y - A binary matrix representing the labels of each example in `X`.
                Row i of `y` corresponds to example i in `X`. Columns of `y`
                define class labels. If y[i, l] = 1 then example i has label l.
                Each record may have multiple labels.
        '''
        if type(X) is not list:
            raise ValueError("`X` must be a list of strings.")
        if type(X[0]) is not str:
            raise ValueError("`X` must be a list of strings.")
        if type(y) is not np.ndarray:
            raise ValueError("`y` must be a binary matrix of type numpy.ndarray.")
        if len(X) != np.shape(y)[0]:
            raise ValueError("Inconsistent number of rows in `X` and `y`. They must be the same.")
        
        self.y = y
        
        for i, x in enumerate(X):
            min_hash_i = self.get_min_hash(x)
            self.lsh.insert(i, min_hash_i)
    
    def predict(self, X):
        '''
        Predict the labels of the input examples.
        Parameters:
            X - A list of strings. Each element defines one training example
                identified by its list index.
        
        Returns:
            A binary matrix representing the predicted labels of each example
            in `X`. Row i of `y` corresponds to example i in `X`. Columns of `y`
            define class labels. If y[i, l] = 1 then example i has label l.
            Each record may have multiple labels.
        '''
        if type(X) is not list:
            raise ValueError("`X` must be a list of strings.")
        if type(X[0]) is not str:
            raise ValueError("`X` must be a list of strings.")
        
        y_pred = np.zeros((len(X), np.shape(self.y)[1]), dtype=np.int64)
        
        for i, x in enumerate(X):
            min_hash = self.get_min_hash(x)
            x_similar_examples = self.lsh.query(min_hash)
            y_pred_i = self.get_majority_labels(x_similar_examples)
            y_pred[i] = y_pred_i
        
        return y_pred
    
    def get_min_hash(self, x):
        '''
        Create a MinHash object for the input example string
        using w-shingling.
        
        Parameters:
            x - A string representing an example.
        
        Returns:
            A datasketch.MinHash object updated with
            the generated w-shingles.
        '''
        # map string x to a set of shingles
        x_shingles = MinHashNearestNeighbor.get_w_shingles(x, self.w)
        min_hash = MinHash(num_perm=self.k)
        for shingle in x_shingles:
            min_hash.update(shingle)
        return min_hash
    
    def get_majority_labels(self, example_indices):
        '''
        Get the labels which appear in at least `label_majority_threshold`
        examples from the provided ones.
        
        Parameters:
            example_indices - Indices of the training examples from which we
                              will collect labels and compute the majority.
        
        Returns:
            A single row binary matrix where column l is 1 if label l is a
            majority label among the provided examples.
        '''
        y_filtered = self.y[example_indices]
        
        # find the proportions of label appearances
        y_freq = np.sum(y_filtered, 0)
        y_freq = y_freq / float(len(example_indices))
        
        # apply label majority threshold
        y_maj = y_freq > self.label_majority_threshold
        
        return y_maj.astype(np.int64)
    
    @staticmethod
    def get_w_shingles(text, w):
        '''
        Extract all fixed size substrings of a string using a sliding window.
        
        Parameters:
            text: Input string.
            w: Size of the sliding window.
        
        Returns:
            A set of w-shingles.
        '''
        shingles = set()
        slides_count = len(text) - w
        for i in range(slides_count + 1):
            shingle = text[i : i + w]
            shingles.add(shingle)
        
        return shingles
    
    @staticmethod
    def get_L(k, threshold):
        '''
        Calculate which value of `L` leads to `threshold` given `k`.
        '''
        return int(round(pow((1. / (1. - threshold)), k)))
    
    @staticmethod
    def get_threshold(k, L):
        '''
        Calculate `threshold` given `k` and `L` of the sketch.
        '''
        return 1. - pow(1. / float(L), 1. / float(k))
    