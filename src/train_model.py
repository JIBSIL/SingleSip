import tensorflow as tf
import shutil
from tensorflow.keras.models import load_model
import shutil
import src.utils as utils

export_model = True


def export_model(model, ticker, filename=""):
    utils.cleanup_zip()
    if not filename:
        filename = f"models/trained_{ticker}"
    model.save(filename)
    shutil.make_archive(filename, "zip", filename)
    print(f"Saved the trained {ticker} weights")


def train_model(
    X_train,
    X_test,
    y_train,
    y_test,
    ticker,
    modelzipfile,
    train_model=True,
    evaluation_data=None,
):
    # evaluation_data shape:
    if evaluation_data is None:
        evaluation_data = (175, 25, 100, 64, f"models/trained_{ticker}")
    layer1, layer_delta, epochs, batchsize, modelzip = evaluation_data

    if train_model:
        # LSTM Model with Optimizations
        model = tf.keras.models.Sequential(
            [
                # Increased LSTM units, added return_sequences for stacking
                tf.keras.layers.LSTM(
                    layer1,
                    return_sequences=True,
                    input_shape=(X_train.shape[1], X_train.shape[2]),
                ),
                tf.keras.layers.Dropout(0.3),
                # Additional LSTM layers
                tf.keras.layers.LSTM(layer1 - layer_delta, return_sequences=True),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.LSTM(layer1 - layer_delta, return_sequences=False),
                tf.keras.layers.Dropout(0.2),
                # Batch Normalization
                tf.keras.layers.BatchNormalization(),
                # Increased Dense layer neurons
                # https://ijisrt.com/wp-content/uploads/2019/06/IJISRT19JU92.pdf
                tf.keras.layers.Dense(64, activation="relu"),
                # Output layer
                tf.keras.layers.Dense(1),
            ]
        )

        # Compile the model with possible optimizer adjustment
        model.compile(optimizer="adam", loss="mean_squared_error")

        # Model summary
        model.summary()

        # Early Stopping Callback
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=20, restore_best_weights=True
        )

        # Adjust the fit method to include callbacks and potentially longer training
        model.fit(
            X_train,
            y_train,
            epochs=epochs,
            batch_size=batchsize,
            validation_data=(X_test, y_test),
            callbacks=[early_stopping],
        )

        # save model
        export_model(model, ticker, modelzip)

        return model
    else:
        print(f"Train_model is false, reading out from zipfile {modelzipfile}...")
        shutil.unpack_archive(modelzipfile, f"trained_{ticker}", "zip")
        model = load_model(f"trained_{ticker}")

        print(f"Loaded trained model on ticker {ticker}")
        return model
