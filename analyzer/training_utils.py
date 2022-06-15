import xgboost as xgb
import pandas as pd 
from pandas import MultiIndex, Int16Dtype
from sklearn.ensemble import RandomForestClassifier

def rf_training_stage(window, training_models):
    '''
    Manage training stage of streaming anomaly detection
    ----------
    Parameters
    window: class training_window
        Sliding window with training data
    training_models: dict
        Trained detector by prefix stored in. Default is randomforest
    ----------
    Return
    training_models
    '''
    pw_window = window.prefix_wise_window()
    for x in pw_window:
        clf  = RandomForestClassifier()
        training_x = pw_window[x][0]
        training_y = pw_window[x][1]
        
        clf.fit(pw_window[x][0],pw_window[x][1])
        if 'detector_%s'%(x) not in training_models:
            training_models['detector_%s'%(x)] =[0,0]
        training_models['detector_%s'%(x)][0] += 1
        training_models['detector_%s'%(x)][1] = clf
    return training_models

def xgb_training_stage(window, training_models):
    '''
    Manage training stage of streaming anomaly detection
    ----------
    Parameters
    window: class training_window
        Sliding window with training data
    training_models: dict
        Trained detector by prefix stored in. Default is randomforest
    ----------
    Return
    training_models
    '''
    pw_window = window.prefix_wise_window()
    for x in pw_window:
        clf  = xgb.XGBClassifier(n_estimators = 100, learning_rate=0.01)
        training_x = pw_window[x][0]
        training_y = pw_window[x][1]
        
        clf.fit(pw_window[x][0],pw_window[x][1])
        if 'detector_%s'%(x) not in training_models:
            training_models['detector_%s'%(x)] =[0,0]
        training_models['detector_%s'%(x)][0] += 1
        training_models['detector_%s'%(x)][1] = clf
    return training_models

