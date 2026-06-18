import pandas as pd
import numpy as np
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
import time, os

print("\n=== Real-Time Traffic Prediction ===")

csv_file = "traffic_data.csv"

while not os.path.exists(csv_file):
    print("Waiting for traffic_data.csv ...")
    time.sleep(2)

print("CSV found! Loading initial data...")


def load_and_clean(filepath):

    df = pd.read_csv(filepath)
    df = df.reset_index().rename(columns={"index": "orig_idx"})  # remembers raw position

    # remove OpenFlow management port
    df = df[df["port"] != 4294967294].copy()

    # convert values
    for col in ["rx_bytes", "tx_bytes", "port", "datapath"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["rx_bytes", "tx_bytes", "port", "datapath"]).reset_index(drop=True)

    # correct ordering
    df = df.sort_values(
        ["datapath", "port", "timestamp"]
    ).reset_index(drop=True)

    # calculate traffic rate
    df["rx_rate"] = (
        df.groupby(["datapath", "port"])["rx_bytes"]
        .diff()
    )

    df["tx_rate"] = (
        df.groupby(["datapath", "port"])["tx_bytes"]
        .diff()
    )

    # remove invalid deltas
    df = df.dropna(subset=["rx_rate", "tx_rate"])

    df = df[
        (df["rx_rate"] >= 0) &
        (df["tx_rate"] >= 0)
    ]

    # previous traffic features
    df["rx_rate_lag1"] = (
        df.groupby(["datapath", "port"])["rx_rate"]
        .shift(1)
    )

    df["tx_rate_lag1"] = (
        df.groupby(["datapath", "port"])["tx_rate"]
        .shift(1)
    )

    df = df.dropna().reset_index(drop=True)

    return df



features = [
    "rx_rate_lag1",
    "tx_rate_lag1",
    "tx_rate",
    "port",
    "datapath"
]

target = "rx_rate"



def transform(df):

    X = df[features].copy()

    # log transform fix for SVR
    X["rx_rate_lag1"] = np.log1p(
        X["rx_rate_lag1"]
    )

    X["tx_rate_lag1"] = np.log1p(
        X["tx_rate_lag1"]
    )

    X["tx_rate"] = np.log1p(
        X["tx_rate"]
    )

    y = np.log1p(df[target])

    return X, y



# initial training

raw = pd.read_csv(csv_file)

data = load_and_clean(csv_file)

X, y = transform(data)

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


model = SVR(
    kernel="rbf",
    C=100,
    gamma="scale",
    epsilon=0.01
)

model.fit(X_scaled, y)


print(
    f"Model trained on {len(data)} rows"
)

print("Live monitoring started...\n")


last_raw_len = len(raw)


while True:

    time.sleep(5)

    new_raw = pd.read_csv(csv_file)


    if len(new_raw) > last_raw_len:

        added = len(new_raw) - last_raw_len

        print(
            f"\n📡 New data detected (+{added} rows)"
        )


        new_data = load_and_clean(csv_file)


        # FIX: select rows by their ORIGINAL position in the raw CSV,
        # not by timestamp or array position. The CSV only ever grows,
        # so orig_idx >= last_raw_len always catches genuinely new rows
        # from every switch and port — regardless of clock time or
        # which group they land in after sorting.
        new_rows = new_data[
            new_data["orig_idx"] >= last_raw_len
        ].copy()

        if len(new_rows) == 0:
            last_raw_len = len(new_raw)
            continue


        X_new, _ = transform(new_rows)

        X_new_scaled = scaler.transform(
            X_new
        )


        predictions = np.expm1(
            model.predict(X_new_scaled)
        )


        print(
            "\nSwitch  Port   Predicted     Actual      Status"
        )
        print(
            "-" * 60
        )


        for i, pred in enumerate(predictions):

            row = new_rows.iloc[i]

            actual = row["rx_rate"]


            if actual < 500_000:
                status = "🟢 Normal"

            elif actual < 50_000_000:
                status = "🟡 High"

            else:
                status = "🔴 Congested"



            print(
                f"{int(row['datapath']):<8}"
                f"{int(row['port']):<7}"
                f"{pred:>12,.0f}"
                f"{actual:>12,.0f}"
                f"   {status}"
            )


        # update counters
        data = new_data
        last_raw_len = len(new_raw)


    else:

        print(
            ".",
            end="",
            flush=True
        )