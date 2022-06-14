import json
import time
from flask import Flask, request,flash
import requests
import copy

app = Flask(__name__)

# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain

class sliding_db:
    def __init__(self, window_size):
        self.window=[]
        self.window_size = window_size

    def update(self,tx):
        if len(self.window) >= self.window_size:
            self.window.pop(0)
        self.window.append(tx)
    
    def invoke_window(self):
        return self.window

window_size=200
sliding_db = sliding_db(window_size)


@app.route('/add_received_transaction', methods=['POST'])
def add_transaction():
    tx_data = request.get_json()
    tx_data = json.dumps(tx_data,ensure_ascii=False)
    tx_data = eval(tx_data)

    sliding_db.update(tx_data)
    added = True

    if not added:
        return "Something wrong event is not added", 400
    
    print(tx_data)
    return "New event is added to the DB", 201



# Uncomment this line if you want to specify the port number in the code
#app.run(debug=True, port=8000)

if __name__ =='__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5001, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0',port=port,debug=True)