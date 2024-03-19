import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
import numpy as np

def calculate_variance(predictions, y_test_unscaled):
    variance_predictions_unscaled = np.var(predictions)
    variance_y_test_unscaled = np.var(y_test_unscaled)

    correlation_coefficient = np.corrcoef(predictions, y_test_unscaled)[0, 1]

    print(f'Predictions variance: {variance_predictions_unscaled}')
    print(f'y_test variance: {variance_y_test_unscaled}')
    print(f'Coorelation coefficient: {correlation_coefficient}')

def get_num_features():
    num_features = 7
    num_features_backtest = num_features - 1
    return num_features, num_features_backtest

def evaluate_model(model, X_test, y_test, scaler, ticker, opt_graph):
    test_loss = model.evaluate(X_test, y_test)
    print(f"Test Loss: {test_loss}")

    predictions_scaled = model.predict(X_test)

    # scaler was trained on data with 12 features
    num_features, num_features_backtest = get_num_features()

    # Create an array of zeros with the appropriate shape
    full_array = np.zeros((predictions_scaled.shape[0], num_features))

    # Replace the first 2 columns of full_array with predictions_scaled
    full_array[:, :2] = predictions_scaled

    # Apply the inverse transformation
    predictions = scaler.inverse_transform(full_array)[:, 0]

    # Calculate the scaled MAE and RMSE for comparison
    mae_scaled = mean_absolute_error(y_test, predictions_scaled)
    rmse_scaled = np.sqrt(mean_squared_error(y_test, predictions_scaled))

    print(f"Scaled Mean Absolute Error: {mae_scaled}")
    print(f"Scaled Root Mean Squared Error: {rmse_scaled}")
    
    y_test_reshaped = y_test.reshape(-1, 1)

    # Create an array of zeros with 7 columns (to add up to 8 features in total)
    zeros_array = np.zeros((y_test.shape[0], num_features_backtest))

    # Concatenate y_test_reshaped with zeros_array to get an array with 8 columns
    full_array = np.concatenate((y_test_reshaped, zeros_array), axis=1)

    # Apply the inverse transformation and select the first column
    y_test_unscaled = scaler.inverse_transform(full_array)[:, 0]
    
    calculate_variance(predictions, y_test_unscaled)
    
    if not opt_graph:
        return num_features, num_features_backtest

    # Plot scaled predictions
    plt.figure(figsize=(10, 6))
    plt.plot(y_test[1:], label="Actual Price (scaled)")
    plt.plot(predictions_scaled[1:], label="Predicted Price (scaled)")
    plt.title(f"{ticker} Price Prediction (scaled)")
    plt.xlabel("Time")
    plt.ylabel("Price (scaled)")
    plt.legend()
    plt.show()

    # Plot unscaled predictions
    plt.figure(figsize=(10, 6))
    # Ensure y_test is also unscaled here if predictions are unscaled

    # y_test_unscaled = scaler.inverse_transform(np.concatenate((y_test.reshape(-1,1), np.zeros((y_test.shape[0], 2))), axis=1))[:, 0]

    plt.plot(y_test_unscaled[1:], label="Actual Price (unscaled)")
    plt.plot(predictions[1:], label="Predicted Price (unscaled)")
    plt.title(f"{ticker} Price Prediction (unscaled)")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.legend()
    plt.show()
    
    return num_features, num_features_backtest
