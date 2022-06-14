from dataclasses import dataclass
import pandas as pd
from pymongo import MongoClient

client = MongoClient('127.0.0.1:27017')

db = client.streaming_events
collect = db.transactions

while True:
    for x in collect.find():
        print(x)
