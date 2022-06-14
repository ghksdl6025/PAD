import pymongo
from pymongo import MongoClient
import time
import json
import requests,os 
from bson.json_util import dumps
import multiprocessing
from functools import partial
import numpy as np
import pandas as pd

'''
1. Initiate bootstrap with generating random transaction and request randomly assigned node to make take the transactions.
2. Assigned miner will check the length of pending transaction and if the length is over 20, it will mine new block

Task 1. will be executed with multiprocessing, in below case 4 processes.
Task 2. is another processes that keep sending GET request to miner to check and mine new block in given time.
'''



conn = MongoClient('127.0.0.1:27017')
# conn.drop_database('blockchaindb')
db = conn.blockchaindb
collect = db.transactions

def request_transaction(dataframe,e_time):
    count = 0
    start_time = time.time()
    node =1

    for nt in dataframe.iterrows():
        nt = nt[1]
        port = 8000+node 
        # port = 5000
        CONNECTED_NODE_ADDRESS = 'http://127.0.0.1:'+str(port)+'/'

        if pd.isna(nt['noise']):
            nt['noise'] = 'Nan'
        post_object = {}
        post_object.update({'ID':nt["ID"]})
        post_object.update({'Activity':nt["Activity"]})
        post_object.update({'Timestamp':nt["Timestamp"]})
        post_object.update({'Noise':nt["noise"]})


        # Submit a transaction
        new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

        requests.post(new_tx_address,
                        json=post_object,
                        headers={'Content-type': 'application/json'})

        time.sleep(e_time)

if __name__=='__main__':

    e_time = 3
    dataframe = pd.read_csv('./data/loan_baseline.pnml_noise_0.049999999999999996_iteration_1_seed_42477_sample.csv')
    request_transaction(dataframe,e_time=3)
    '''
    Multi processor for multiple event generator
    '''
    # processes =4
 
    # procs =[]
    # for number in range(processes):
    #     proc = multiprocessing.Process(target=request_transaction, name ='Client{}'.format(number+1), args=(e_time,))
    #     procs.append(proc)
    #     proc.start()
    # proc.start()
    # procs.append(proc)

    # for proc in procs:
    #     proc.join()