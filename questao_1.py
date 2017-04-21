#By Felipe, Paulo e Debora

import pandas as pd
import numpy as np
import math as m
import pickle

class ClusterMaker:

    
    #n is the number of elements to be clustered
    #k is the number of clusters
    #p is the number of views
    #q is the number of elements of a cluster prototype
    def __init__(self, filename, k, q, m, s, read_files=False):
        self.k = k
        self.q = q
        self.p = 2
        self.m = m
        self.s = s
        
        if read_files:
            print 'Reading input file'
            self.read_from_csv(filename)
            ClusterMaker.print_data_overview(self.raw_data)

            #Create the separated views
            self.create_views()

            #Create the dissimilarity matrix for both views
            self.diss_matrix_1 = ClusterMaker.calculate_diss_matrix(self.view_1)
            self.diss_matrix_2 = ClusterMaker.calculate_diss_matrix(self.view_2)
        else:
            print 'Loading previous matrices'
            self.diss_matrix_1 = pickle.load(open('diss_matrix_1.pickle','rb'))
            self.diss_matrix_2 = pickle.load(open('diss_matrix_1.pickle','rb'))

        self.diss = [self.diss_matrix_1, self.diss_matrix_2]
        
        print 'Dissimilarity matrices calculated'
        self.n = np.shape(self.diss_matrix_1)[0]
        
    def run_clustering(self):
        self.initialize_clustering()
    
    def read_from_csv(self, filename):
        rd = pd.read_csv(filename, sep=",", header=2)
        rd = rd.values #Numpy array
        self.raw_data = rd

    def create_views(self):
        size_view_1 = 9
        size_view_2 = 10
        num_rows = np.shape(self.raw_data)[0]
        self.view_1 = self.raw_data[np.ix_(range(num_rows),range(size_view_1))]
        self.view_2 = self.raw_data[np.ix_(range(num_rows),range(size_view_1, size_view_2))]

    def initialize_clustering(self):
        n = self.n
        k = self.k
        p = self.p
        q = self.q
        
        self.U = np.ones((n, k))
        self.Lambda = np.ones((p, k))

        #shuffle indexes to randomly initialize cluster prototypes
        all_indexes = range(n)
        np.random.shuffle(all_indexes)

        self.G = np.zeros((k, q))

        for i in xrange(self.k):
            self.G[i] = np.array(all_indexes[i*q:(i+1)*q])
        

    def dist_to_cluster(self, elem_index, cluster_index):
        summ = 0
        for p in xrange(self.p):
            partial_sum = 0
            for j in xrange(self.q):
                cluster = self.G[cluster_index]
                partial_sum += self.diss[p][elem_index, cluster[j]]
            summ += self.Lambda[p][cluster_index]*partial_sum
        return summ

    def cost_by_cluster(self, cluster_index):
        summ = 0
        for i in xrange(self.n):
                summ += pow(self.U[i][cluster_index],self.m)*self.dist_to_cluster(i, cluster_index)
        return summ
    
    def cost(self):
        summ = 0
        for k in xrange(self.k):
            summ += self.cost_by_cluster(k)
        return summ
    
    def update_U(self):
        for k in xrange(self.k):
            for i in xrange(self.n):
                summ = 0
                pot_term = 1.0/(self.m - 1.0)
                for h in xrange(self.k):
                    summ += pow(self.dist_to_cluster(i, k)/self.dist_to_cluster(i, h), pot_term) 
                
                self.U[i][k] = pow(summ, -1)

    def part_lambda_dist(self, view_index, cluster_index):
        summ = 0
        for i in xrange(self.n):
            partial_sum = 0
            for j in xrange(self.q):
                cluster = self.G[cluster_index]
                partial_sum += self.diss[view_index][i, cluster[j]]
            summ += pow(self.U[i][cluster_index], self.m)*partial_sum
        return summ
    
    def update_Lambda(self):
        for i in xrange(self.p):
            for k in xrange(self.k):
                prod = 1
                for j in xrange(self.p):
                    prod *= self.part_lambda_dist(j, k)
                prod = pow(prod, 1.0/float(self.p))
                self.Lambda[i][k] = prod/self.part_lambda_dist(i, k)

    def part_G_sum(self, element_index, cluster_index):
        summ = 0
        for i in xrange(self.n):
            partial_sum = 0
            for j in xrange(self.p):
                partial_sum += self.Lambda[j][cluster_index]*self.diss[j][i][element_index]
            summ += pow(self.U[i][cluster_index], self.m)*partial_sum
        return summ
    
    def update_G(self):
        all_indexes = range(self.n)
        all_index_dist = [[i, 0] for i in all_indexes]
        for k in xrange(self.k):
            len_id = len(all_index_dist)
            for j in xrange(len_id):
                all_index_dist[j][1] = self.part_G_sum(all_index_dist[j][0], k)
            all_index_dist = sorted(all_index_dist, key= lambda x : x[1])
            self.G[k] = np.array([a[0] for a in all_index_dist[:self.q]])
            del all_index_dist[:self.q]
    
    @staticmethod
    def cvt_np_array(matrix):
        if type(matrix) != np.ndarray:
            matrix = np.array(matrix)
        return matrix

    @staticmethod
    def print_data_overview(raw_data):    
        raw_data = ClusterMaker.cvt_np_array(raw_data)
        
        num_elems = np.shape(raw_data)[0]
        num_vars = np.shape(raw_data)[1]

        print 'Numero de elementos:', num_elems
        print 'Numero de variaveis:', num_vars

    @staticmethod
    def euclid_dist(vect1, vect2):
        if len(vect1) != len(vect2):
            raise ValueError('The size of the vectors must be equal')

        vect1 = ClusterMaker.cvt_np_array(vect1)
        vect2 = ClusterMaker.cvt_np_array(vect2)
        
        diff = vect1 - vect2
        
        return np.sqrt(np.dot(diff, diff))

    @staticmethod
    def calculate_diss_matrix(raw_data):
        raw_data = ClusterMaker.cvt_np_array(raw_data)
        
        num_elems = np.shape(raw_data)[0]
        diss_matrix = np.zeros((num_elems, num_elems))

        for i in xrange(num_elems):
            for j in xrange(num_elems):
                elem1 = raw_data[i]
                elem2 = raw_data[j]
            
                diss_matrix[i][j] = ClusterMaker.euclid_dist(elem1, elem2)    

        return diss_matrix
    
#Begin

cm = ClusterMaker('data/segmentation.data.txt', 7, 3, 1.6, 1, read_files=True) 
cm.run_clustering()
