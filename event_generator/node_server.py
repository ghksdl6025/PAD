from hashlib import sha256
import json
import time
import pymongo
from pymongo import MongoClient
from flask import Flask, request,flash
import requests
import copy

app = Flask(__name__)

# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain

def add_new_transaction(self, transaction):
    tx_hash = sha256(json.dumps(transaction).encode()).hexdigest()
    if tx_hash not in self.tx_ids:
        self.unvalidated_transactions[tx_hash] = transaction
        self.tx_ids.add(tx_hash)
    return transaction

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()

    # required_fields = ["ID",'Timestamp','Activity', 'Noise']
    # for field in required_fields:
    #     if not tx_data.get(field):
    #         print('WHAT', field)
    #         return "Invalid transaction data", 404

    record_in_db(tx_data,'Transaction initiated')

    return "Success", 201


def record_in_db(transaction,activity,mode='transaction',qc_id=None):
    '''
    Record invoked activity and transaction in database
    mode : default = transaction
    1)transaction
    2)block
    '''

    # conn = MongoClient('127.0.0.1:27017')
    client = MongoClient('172.28.2.1:27017')

    db = client.streaming_events
    collect = db.transactions

    if mode =='transaction':
        dbtx = copy.deepcopy(transaction)
        dbtx['Transaction ID'] = sha256(json.dumps(transaction).encode()).hexdigest()
        dbtx['Time in DB'] = time.time()
        dbtx['Node'] = 'Node '+ str(port-8000)
        dbtx['activity'] = activity
        collect.insert_one(dbtx)

    elif mode =='block':
        dbtx={}
        tx_ids = list(transaction.keys())
        dbtx['Transaction ID'] = tx_ids
        dbtx['Time in DB'] = time.time()
        dbtx['Node'] = 'Node '+ str(port-8000)
        dbtx['activity'] = activity
        collect.insert_one(dbtx)

    elif mode == 'validation':
        dbtx={}
        dbtx['Transaction ID'] = transaction
        dbtx['Time in DB'] = time.time()
        dbtx['Node'] = 'Node '+ str(port-8000)
        dbtx['activity'] = activity
        dbtx['Quality Control ID'] = qc_id
        collect.insert_one(dbtx)

    return "Success", 201



# Uncomment this line if you want to specify the port number in the code
#app.run(debug=True, port=8000)

if __name__ =='__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0',port=port,debug=True)