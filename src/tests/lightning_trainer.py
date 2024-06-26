# import numpy as np
# import pandas as pd
# import copy
# from pathlib import Path
import torch
import torch.nn as nn

import lightning.pytorch as pl
from lightning.pytorch.callbacks import EarlyStopping, LearningRateMonitor
from lightning.pytorch.loggers import TensorBoardLogger
from lightning.pytorch.tuner import Tuner
from lightning.pytorch import Trainer

import pytorch_forecasting
# from pytorch_forecasting import Baseline, TemporalFusionTransformer, TimeSeriesDataSet
from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
# from pytorch_forecasting.data import GroupNormalizer
# from pytorch_forecasting.metrics import SMAPE, PoissonLoss, QuantileLoss

import matplotlib.pyplot as plt

# TEST CASE: using pytorch lightning to determine lr and train
# majority of this code is adapted from https://www.kaggle.com/code/shreyasajal/pytorch-forecasting-for-time-series-forecasting

# this integrated function will probably be shifted if the module is expanded
def prepare_and_train(df_train, model_name):
    
    max_prediction_length = 1
    max_encoder_length = 27
    #training_cutoff = df_train['date_block_num'].max() - max_prediction_length

    training = TimeSeriesDataSet(
        df_train,
        time_idx='IDX',
        target="PRICE",
        group_ids=["3_day_avg_price", "tsi", "rsi", "sharpe_ratio", "Bollinger_Upper", "Bollinger_Lower"],
        min_encoder_length=0,  
        max_encoder_length=max_encoder_length,
        min_prediction_length=1,
        max_prediction_length=max_prediction_length,
        static_categoricals=[],
        time_varying_unknown_categoricals=[],
        time_varying_unknown_reals=[], #['PRICE'],
        add_relative_time_idx=True,
        add_target_scales=True,
        add_encoder_length=True,
        allow_missing_timesteps=True
    )
    
    validation = TimeSeriesDataSet.from_dataset(training, df_train, stop_randomization=True)
    
    if model_name != None and model_name != "":
        model = TemporalFusionTransformer.load_from_checkpoint(model_name)
        return model, validation

    batch_size = 128
    train_dataloader = training.to_dataloader(train=True, batch_size=batch_size)
    val_dataloader = validation.to_dataloader(train=False, batch_size=batch_size)# * 10)
    
    # configure network and trainer
    pl.seed_everything(42)
    trainer = Trainer(
        # clipping gradients is a hyperparameter and important to prevent divergance
        # of the gradient for recurrent neural networks
        gradient_clip_val=0.1,
    )


    tft = TemporalFusionTransformer.from_dataset(
        training,
        # not meaningful for finding the learning rate but otherwise very important
        learning_rate=0.03,
        hidden_size=16,  # most important hyperparameter apart from learning rate
        # number of attention heads. Set to up to 4 for large datasets
        attention_head_size=1,
        dropout=0.1,  # between 0.1 and 0.3 are good values
        hidden_continuous_size=8,  # set to <= hidden_size
        output_size=1,  # 7 quantiles by default
        loss=pytorch_forecasting.metrics.RMSE(),
        # reduce learning rate if no improvement in validation loss after x epochs
        reduce_on_plateau_patience=4,
    )
    print(f"Number of parameters in network: {tft.size()/1e3:.1f}k")
    
    # find optimal learning rate
    tuner = Tuner(trainer)
    res = tuner.lr_find(
        model=tft,
        train_dataloaders=train_dataloader,
        val_dataloaders=val_dataloader,
        max_lr=0.1,
        min_lr=1e-7,
    )

    print(f"suggested learning rate: {res.suggestion()}")
    # fig = res.plot(show=True, suggest=True)
    # fig.show()
    
    early_stop_callback = EarlyStopping(monitor="val_loss", min_delta=1e-7, patience=10, verbose=False, mode="min")
    lr_logger = LearningRateMonitor()  
    logger = TensorBoardLogger("lightning_logs") 

    trainer = pl.Trainer(
        max_epochs=30,
        enable_model_summary=True,
        gradient_clip_val=0.1,
        limit_train_batches=30,  
        callbacks=[lr_logger, early_stop_callback],
        logger=logger,
    )


    tft = TemporalFusionTransformer.from_dataset(
        training,
        learning_rate=5e-7,
        hidden_size=16,
        attention_head_size=1,
        dropout=0.1,
        hidden_continuous_size=8,
        output_size=1, 
        loss=pytorch_forecasting.metrics.RMSE(),
        log_interval=0,  
        reduce_on_plateau_patience=4,
    )
    print(f"Number of parameters in network: {tft.size()/1e3:.1f}k")
    
    trainer.fit(
        tft,
        train_dataloaders=train_dataloader,
        val_dataloaders=val_dataloader,
    )
    
    best_model_path = trainer.checkpoint_callback.best_model_path
    best_tft = TemporalFusionTransformer.load_from_checkpoint(best_model_path)
    
    # calcualte root mean squared error on validation set
    actuals = torch.cat([y[0] for x, y in iter(val_dataloader)]).to("cuda")
    val_predictions = best_tft.predict(val_dataloader)
    
    criterion = nn.MSELoss()
    print(torch.sqrt(criterion(actuals, val_predictions)))
            
    return best_tft, validation

# def load_and_measure_loss(model_path):
#     best_tft = TemporalFusionTransformer.load_from_checkpoint(model_path)
    