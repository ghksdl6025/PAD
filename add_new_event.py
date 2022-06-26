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

def request_transaction(dataframe,e_time):

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

        request_result= requests.post(new_tx_address,
                        json=post_object,
                        headers={'Content-type': 'application/json'})
        print('------- New event distributed -------')
        print(request_result.content)
        print('-------------------------------------')
        print('\n')

        port2 = 8002
        running_cases = requests.get('http://127.0.0.1:%s/get_runningcases'%(str(port2)))
        json_result = json.loads(running_cases.content)
        print('---------- Detection Result ----------')
        print(pd.DataFrame(json_result))
        print('--------------------------------------')

        time.sleep(e_time)

def download_anomaly_result(group):
    '''
    group = Running / Finished
    '''
    # port = 5001
    node =2
    port = 8000+node 
    CONNECTED_NODE_ADDRESS = 'http://127.0.0.1:'+str(port)+'/'
    new_tx_address = "{}/download_predictions".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_tx_address,
                        json={'target':group},
                        headers={'Content-type': 'application/json'})
    os.system('docker cp pad-analyzer-1:/app/%s.csv ./'%(group))

def set_threshold(threshold):
    '''
    group = Running / Finished
    '''
    # port = 5001
    node =2
    port = 8000+node 
    CONNECTED_NODE_ADDRESS = 'http://127.0.0.1:'+str(port)+'/'
    new_tx_address = "{}/set_threshold".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_tx_address,
                        json={'threshold':threshold},
                        headers={'Content-type': 'application/json'})


if __name__=='__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    e_time = 0
    parser.add_argument('-m', '--mode', default='streaming', type=str, help='streaming or stop events stream')

    if parser.parse_args().mode == 'streaming':
        print('Please type the data')
        data = input()
        print('Please type the threshold')
        threshold = input()
        args = parser.parse_args()
        dataframe = pd.read_csv(data)
        set_threshold(threshold)
        request_transaction(dataframe,e_time=e_time)

    elif parser.parse_args().mode == 'stop':
        print('------- Download running cases detection Result -------')
        target ='Running'
        download_anomaly_result(group=target)        
        print('.... Done')
        print('\n')

        print('------- Download finished cases detection Result -------')
        target ='Finished'
        download_anomaly_result(group=target)        
        print('.... Done')
    

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