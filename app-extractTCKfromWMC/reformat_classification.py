#!/usr/bin/env python3

from argparse import Namespace
import os,sys
import json
import numpy as np
import nibabel as nib
import scipy.io as sio
import pandas as pd

def save_info(names,indices):
    
    df_index = pd.DataFrame()
    df_index['Index'] = indices
    df_index.to_csv('index.csv',index=False,header=False)
    
    df_names = pd.DataFrame()
    df_names['Name'] = names
    df_names.to_csv('names.csv',index=False,header=False)
    
def extract_indices(classification):

    print('extracting tract names from classification structure')
    indices =  list(classification['classification'][0]['index'][0][0])
    
    return indices

def extract_names(classification):

    print('extracting tract indices from classification structure')
    names = [ f[0] for f in classification['classification'][0]['names'][0][0] ]
    
    return names
    
def load_classification(classification_path):
    
    print('loading classification structure')
    classification = sio.loadmat(classification_path)
    
    return classification    

def main():
    
    with open('config.json','r') as confg_f:
        config = json.load(confg_f)
    
    # identify path from config
    classification_path = config['classification']
    
    # load classification structure
    classification = load_classification(classification_path=classification_path)
    
    # extract indices
    indices = extract_indices(classification=classification)
    
    # extract names
    names = extract_names(classification=classification)
    
    # save reformatted classification
    save_info(names=names,indices=indices)
    
if __name__ == "__main__":
    main()
