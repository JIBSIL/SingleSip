# basic utils that don't fit into any specific class

import os
import shutil
import pathlib

# delete trained_LTC folder
def cleanup_last_generation():
    if os.path.exists('trained_LTC'):
        shutil.rmtree('trained_LTC')
        print('Deleted trained_LTC folder (it will be regenerated with new weights)')

# get all models in models/ folder
def get_models(include_eval):
    models = []
    
    for file in list(pathlib.Path('models').iterdir()):
        if file.suffix == '.zip':            
            filepath = f'{file}'.replace('\\', '/')
            models.append(filepath)
    
    if include_eval:
        for file in list(pathlib.Path('models/eval').iterdir()):
            if file.suffix == '.zip':
                filepath = f'{file}'.replace('\\', '/')
                models.append(filepath)
    
    return models

# delete trained_ltc.zip
def cleanup_zip():
    if os.path.exists('trained_LTC.zip'):
        os.remove('trained_LTC.zip')
        print('Deleted trained_LTC.zip')