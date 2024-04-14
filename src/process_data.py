import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import numpy as np


# technical indicator fns
def calculate_rsi(data, window=14):
    delta = data["PRICE"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_tsi(data, high_window=25, low_window=13):
    momentum = data["PRICE"].diff(1)
    smooth_momentum = momentum.ewm(span=high_window).mean()
    double_smooth_momentum = smooth_momentum.ewm(span=low_window).mean()

    absolute_momentum = np.abs(momentum).ewm(span=high_window).mean()
    double_smooth_abs_momentum = absolute_momentum.ewm(span=low_window).mean()

    tsi = 100 * (double_smooth_momentum / double_smooth_abs_momentum)
    return tsi


def calculate_ema(data, window):
    return data["PRICE"].ewm(span=window, adjust=False).mean()


def calculate_bollinger_bands(data, window):
    sma = data["PRICE"].rolling(window=window).mean()
    std = data["PRICE"].rolling(window=window).std()
    bollinger_upper = sma + (std * 2)
    bollinger_lower = sma - (std * 2)
    return bollinger_upper, bollinger_lower


def calculate_macd(data, short_window, long_window):
    short_ema = calculate_ema(data, short_window)
    long_ema = calculate_ema(data, long_window)
    return short_ema - long_ema


def process_data(stats):
    # print(f'{len(stats)} datapoints were returned')
    df_stats = pd.DataFrame(stats, columns=["TIMESTAMP", "PRICE"])
    df_stats["TIMESTAMP"] = pd.to_datetime(df_stats["TIMESTAMP"], unit="ms")

    df_merged = df_stats.copy()
    return df_merged


def add_technical_indicators(df_stats, window, data_train_test):
    df_merged = df_stats.copy()

    # Add RSI to the dataframe
    df_merged["rsi"] = calculate_rsi(df_merged)

    # Add TSI to the dataframe
    df_merged["tsi"] = calculate_tsi(df_merged)

    # sharpe ratio
    df_merged["daily_return"] = df_merged["PRICE"].pct_change()

    # Calculate mean return and standard deviation of returns
    mean_return = df_merged["daily_return"].mean()
    std_return = df_merged["daily_return"].std()

    # Assuming a risk-free rate of 0, though this can be adjusted
    risk_free_rate = 0

    # Calculate Sharpe Ratio - Annualized (assuming 252 trading days)
    df_merged["sharpe_ratio"] = (
        (mean_return - risk_free_rate) / std_return * np.sqrt(365)
    )

    # Standard MACD uses 12-day EMA and 26-day EMA
    df_merged["MACD"] = calculate_macd(df_merged, 12, 26)
    # 20-day EMA
    df_merged["EMA_20"] = calculate_ema(df_merged, 20)
    # 20-day Bollinger Bands
    (
        df_merged["Bollinger_Upper"],
        df_merged["Bollinger_Lower"],
    ) = calculate_bollinger_bands(df_merged, 20)

    # Calculate 3-day moving averages
    df_merged["3_day_avg_price"] = df_merged["PRICE"].rolling(window=window).mean()

    # Drop initial rows where moving average can't be calculated
    df_merged.dropna(inplace=True)

    # Normalize the features and target
    scaler = MinMaxScaler()
    basic = df_merged[["PRICE"]]
    features = df_merged[
        [
            "3_day_avg_price",
            "tsi",
            "rsi",
            "sharpe_ratio",
            "Bollinger_Upper",
            "Bollinger_Lower",
        ]
    ]

    features.fillna(method="bfill", inplace=True)

    df_for_scaling = pd.concat([basic, features], axis=1)

    scaled_values = scaler.fit_transform(df_for_scaling)
    df_scaled = pd.DataFrame(
        scaled_values, columns=df_for_scaling.columns, index=df_for_scaling.index
    )

    total_len_delta = (
        df_stats["TIMESTAMP"][len(df_stats) - 1] - df_stats["TIMESTAMP"][0]
    )
    print(f"Total length of dataset: {total_len_delta}")
    print(f"Length of test dataset: {total_len_delta * data_train_test}")
    
    df_scaled["IDX"] = range(0, len(df_scaled))

    return df_scaled, scaler


def create_dataset(X, look_back=1):
    Xs, ys = [], []
    for i in range(len(X) - look_back):
        v = X.iloc[i : (i + look_back)].values
        Xs.append(v)
        ys.append(X.iloc[i + look_back, 0])
    return np.array(Xs), np.array(ys)


def prepare_training_dataset(df_scaled, lookback, split_length, shuffle=False):
    # supervised learning format conversion

    # Selecting features and target
    features = df_scaled[
        [
            "3_day_avg_price",
            "tsi",
            "rsi",
            "sharpe_ratio",
            "Bollinger_Upper",
            "Bollinger_Lower",
        ]
    ]
    target = df_scaled[["PRICE"]]

    # Create the dataset for supervised learning
    X, y = create_dataset(pd.concat([target, features], axis=1), lookback)

    # Parameters
    # chunk_size = int(len(X) * split_length)
    num_chunks = 1 / split_length

    # Create a list of indices
    indices = np.arange(len(X))

    # Split indices into chunks, keeping the order within each chunk
    chunked_indices = np.array_split(indices, num_chunks)

    # chunked_indices.pop(0)
    # chunked_indices.pop(0)

    # Shuffle the chunks (disabled UNLESS you want to test on different parts of the price)
    if shuffle:
        np.random.shuffle(chunked_indices)

    # Concatenate the shuffled chunks back
    shuffled_indices = np.concatenate(chunked_indices)

    X_shuffled = X[shuffled_indices]
    y_shuffled = y[shuffled_indices]

    # Split into training and testing sets
    split_point = int(len(X_shuffled) * (1 - split_length))
    X_train, X_test = X_shuffled[:split_point], X_shuffled[split_point:]
    y_train, y_test = y_shuffled[:split_point], y_shuffled[split_point:]

    print(f"X_train shape: {X_train.shape}")

    return X_train, X_test, y_train, y_test
