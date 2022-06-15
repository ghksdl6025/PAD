import json
from flask import Flask, request,flash, Response
import pandas as pd
import utils
from encoding import prefix_bin
from sklearn.metrics import classification_report, accuracy_score
from tqdm import tqdm
import sliding_window
import training_utils
import datetime, time
import importlib
importlib.reload(sliding_window)

app = Flask(__name__)

# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain

class sliding_db:
    def __init__(self):
        self.window=[]

    def update(self,tx):
        if len(self.window) >= self.window_size:
            self.window.pop(0)
        self.window.append(tx)
    
    def invoke_window(self):
        return self.window


# Parameters
enctype = 'Index-base'
threshold = 0.01
key_pair = {
'ID':'caseid',
'Activity':'activity',
'Timestamp':'ts',
}
catatars= ['activity']

# Sliding window for training setting
window_size = 100
retraining_size = 20
training_window = sliding_window.training_window(window_size,retraining_size)

class online_pad:
    def __init__(self):
        self.case_dict ={}
        self.training_models ={}
        self.resultdict ={}
        self.acc_dict ={}
        self.prefix_wise_window = {}
        self.finishedcases = set()

    def invoke_result(self):
        return self.resultdict

    def predict_activity_proba(self, last_event):
        '''
        Predict next activity prediction 
        
        Parameters
        ----------
        last_event: case_bin
        
        Return
        ----------
        modelid, prediction
        
        '''
        feature_matrix = self.prefix_wise_window['window_%s'%(last_event.prefix_length)][0].columns.values

        current_event = utils.readjustment_training(last_event.encoded, feature_matrix)
        current_event = pd.Series(current_event).to_frame().T
        prediction = [self.training_models['detector_window_%s'%(last_event.prefix_length)][1].predict_proba(current_event), 
                        self.training_models['detector_window_%s'%(last_event.prefix_length)][1].classes_]
        modelid = self.training_models['detector_window_%s'%(last_event.prefix_length)][0]
    
        return modelid, prediction

    def anomaly_checker(self, event, threshold):
        prediction_label = 'Normal'
        predictions = list(event.predicted.values())[0][0]
        predictions_proba = predictions[0][0]
        predictions_value = list(predictions[1])
        if predictions  == 'Not Available':
            prediction_label = 'Not Available'
        else:
            if event.true_label in predictions_value:
                labelidx = predictions_value.index(event.true_label)

                if predictions_proba[labelidx] <threshold:
                    prediction_label = 'Anomalous'
            else:
                prediction_label = 'Anomalous'

        return prediction_label

    def access_predictions(self, group):
        if group =='Running':
            target = self.case_dict
        elif group == 'Finished':
            target = self.resultdict

        events_list= []
        for x in target.keys():
            for y in target[x]:
                event = {}
                for att in y.event.keys():
                    event.update({att: y.event[att]})
                    if att == 'ts':
                        event.update({att: y.event[att].strftime("%d-%m-%Y %H:%M:%S")})
                event.update({'anomaly':y.anomaly})
                event.update({'caseid':y.caseid})
                events_list.append(event)
        df = pd.DataFrame(events_list)
        return df


    def save_event_prep(self, tx_data):
        print('Running cases: %s'%(len(self.case_dict)))
        nt = {}
        for t in key_pair.keys():
            nt.update({t:tx_data[t]})

        utils.dictkey_chg(nt, key_pair)
        # Event stream change dictionary keys
        nt['ts'] = nt['ts'][:-4]
        print(nt)
        # Check label possible

        # Initialize case by prefix length
        caseid = nt['caseid']
        nt.pop('caseid')

        case_bin = prefix_bin(caseid, nt)

        if caseid not in list(self.case_dict.keys()):
            self.case_dict[caseid] = []
            case_bin.set_prefix_length(1)
            
        elif caseid in self.finishedcases:
            return 'Finished'

        else:
            case_bin.set_prefix_length(len(self.case_dict[caseid])+1)
            case_bin.set_prev_enc(self.case_dict[caseid][-1])

        # Encode event and cases and add to DB
        ts = case_bin.event['ts']
        case_bin.update_encoded(catattrs=catatars,enctype=enctype)

        # Set current activity as outcome of previous event
        if case_bin.prefix_length != 1:
            case_bin.prev_enc.update_truelabel(nt['activity'])

        # First prediction for current event

        last_event = case_bin
        modelid = 'None'
        prediction = 'Not Available'

        if len(training_window.getAllitems()) !=0:
            if 'window_%s'%(last_event.prefix_length) in list(self.prefix_wise_window.keys()) and 'detector_window_%s'%(last_event.prefix_length) in self.training_models.keys():
                modelid, prediction = self.predict_activity_proba(last_event)
        case_bin.update_prediction((modelid, (prediction,ts)))        
        case_bin.update_anomaly(self.anomaly_checker(case_bin, threshold))

        # Update training window and finish the case
        if nt['activity'] == 'End':
            training_window.update_window({caseid: self.case_dict[caseid]})        
            if training_window.retraining == training_window.retraining_count:            
                self.training_models = training_utils.rf_training_stage(training_window, self.training_models)

                self.prefix_wise_window = training_window.prefix_wise_window()
                
            self.resultdict[caseid] = self.case_dict[caseid]
            self.case_dict.pop(caseid)

            for x in self.case_dict:
                last_event = self.case_dict[x][-1]
                modelid = 'None'
                prediction = 'Not Available'

                if len(training_window.getAllitems()) !=0:
                    prefix_wise_window2 = training_window.prefix_wise_window()
                    if 'window_%s'%(last_event.prefix_length) in list(prefix_wise_window2.keys()) and 'detector_window_%s'%(last_event.prefix_length) in self.training_models.keys():
                        modelid, prediction = self.predict_activity_proba(last_event)

                self.case_dict[x][-1].update_prediction((modelid, (prediction,ts)))     
                self.case_dict[x][-1].update_anomaly(self.anomaly_checker(case_bin, threshold))   
            training_window.reset_retraining_count()
        else:
            self.case_dict[caseid].append(case_bin)

online_analyzer = online_pad()

@app.route('/download_predictions', methods=['POST'])
def send_pad_result():
    group = request.get_json()['target']
    result =online_analyzer.access_predictions(group).to_json(orient="records")
    online_analyzer.access_predictions(group).to_csv('%s.csv'%(group), index=False)
    
    return Response(result, mimetype='application/json')

@app.route('/get_resultdict', methods=['GET'])
def get_resultdict():
    resultdict = online_analyzer.invoke_result()
    # chain_data = []
    # for block in blockchain.chain:
    #     chain_data.append(block.__dict__)
    return json.dumps({"length": len(resultdict),
                       "resultdict": resultdict})

@app.route('/add_received_transaction', methods=['POST'])
def add_transaction():
    tx_data = request.get_json()
    tx_data = json.dumps(tx_data,ensure_ascii=False)
    tx_data = eval(tx_data)

    # sliding_db.update(tx_data)
    # added = True
    online_analyzer.save_event_prep(tx_data=tx_data)
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