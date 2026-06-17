# Machine Learning-Based Network Traffic Prediction in SDN

A closed-loop system where a Software-Defined Networking (SDN) controller monitors its own network traffic, trains machine learning models on the collected data, and classifies live traffic as **Normal**, **High**, or **Congested** in real time.

**Course:** Networking — Module 2 Project
**Institution:** University of Trento — MSc Information Engineering

---

## Overview

Traditional networks are reactive — they respond to congestion only after packets are already lost. This project makes the network **proactive** by combining:

- **SDN (Software-Defined Networking):** a Ryu controller centrally monitors all switches
- **Machine Learning:** four models are trained to predict and classify traffic load

The Ryu controller collects port statistics every 5 seconds, logs them to a CSV file, and a machine learning pipeline trains on this data to classify network state in real time.

---

## System Architecture

```
<img width="630" height="330" alt="topology" src="https://github.com/user-attachments/assets/c8cace21-6627-4f48-b6f0-44eef47699e5" />

```

- **2 hosts** (h1, h2) generate traffic
- **2 OpenFlow switches** (s1, s2) forward packets
- **Ryu controller** collects statistics every 5 seconds
- (**ML pipeline** classifies traffic in real time)

---

## Requirements

- **ComNetsEmu** virtual machine (includes Mininet, Ryu, Open vSwitch)
- **Python 3** with the following libraries:
  - pandas
  - numpy
  - scikit-learn
  - matplotlib

Install the Python libraries if needed:

```bash
pip3 install pandas numpy scikit-learn matplotlib
```

---

## File Structure

| File | Purpose |
|------|---------|
| `ryu_csv_logger.py` | Ryu controller — collects traffic statistics and logs to CSV |
| `sdn_topology.py` | Builds the Mininet network (2 hosts, 2 switches) |
| `generate_traffic.py` | Generates ICMP and TCP traffic between hosts |
| `train_svm_model.py` | Trains and compares 4 ML models |
| `real_time_predict.py` | Live traffic prediction and classification |
| `analyze_traffic.py` | Plots traffic graphs and basic analysis |
| `model_comparison_results.csv` | Saved model comparison results |

---

## Step-by-Step Installation and Run Guide

The demo uses **4 terminals**. Open them inside the ComNetsEmu VM and navigate to the project folder in each:

```bash
cd ~/comnetsemu/examples/traffic_prediction_final
```

### Step 0 — Clean any previous sessions

```bash
sudo mn -c
sudo pkill -f ryu
```

### Step 1 — Terminal 1: Start the Ryu Controller

```bash
sudo ryu-manager ryu_csv_logger.py ryu.app.simple_switch_13 --ofp-tcp-listen-port 6633
```

Wait until you see the line ending with `OFPHandler`. The controller is now running. Leave this terminal open.

### Step 2 — Terminal 2: Start the Network

```bash
sudo mn --controller=remote,ip=127.0.0.1,port=6633 --switch=ovsk,protocols=OpenFlow13 --topo=linear,2 --mac
```

When the `mininet>` prompt appears, test connectivity:

```
mininet> h1 ping -c 3 10.0.0.2
```

You should see **0% packet loss**, confirming the network is working.

### Step 3 — Terminal 3: Watch Data Collection (optional)

```bash
watch -n 2 wc -l traffic_data.csv
```

This shows the CSV growing as the controller logs traffic.

### Step 4 — Terminal 2: Generate Traffic

Generate traffic at realistic rates (run each line one after another):

```
mininet> h2 iperf -s &
mininet> h1 iperf -c 10.0.0.2 -t 30 -b 1M
mininet> h1 iperf -c 10.0.0.2 -t 30 -b 5M
mininet> h1 iperf -c 10.0.0.2 -t 30 -b 100M
mininet> h1 iperf -c 10.0.0.2 -t 30 -b 500M
```

These bandwidth values simulate real-world scenarios:
- `1M` — light browsing
- `5M` — HD streaming
- `100M` — heavy download
- `500M` — network congestion

### Step 5 — Terminal 4: Train the Models

```bash
python3 train_svm_model.py
```

This trains 4 models and prints a comparison table, then saves results to `model_comparison_results.csv`.

### Step 6 — Terminal 4: Run Live Prediction

```bash
python3 real_time_predict.py
```

This watches for new traffic and classifies it live. Generate more traffic in Terminal 2 to see the status change between Normal, High, and Congested.

### Step 7 — Shutdown

```
mininet> exit          (in Terminal 2)
Ctrl + C               (in Terminal 4, then Terminal 1)
sudo mn -c             (final cleanup)
```

---

## Machine Learning Approach

**Target:** `rx_rate` — delta bytes per 5-second interval (actual throughput, not cumulative counters)

**Features:**
- `rx_rate_lag1`, `tx_rate_lag1` — previous interval values (temporal context)
- `tx_rate`, `port`, `datapath`

**Key techniques:**
- **Management port filtering** — port 4294967294 (OFPP_LOCAL) removed at source and in preprocessing
- **Log transform** — `np.log1p` compresses the large value range so SVR works correctly
- **70/30 train-test split** with StandardScaler normalization

### Model Comparison Results

| Model | MAE (bytes) | R² |
|-------|-------------|-----|
| Decision Tree | 86,489 | 0.9934 |
| Random Forest | 99,023 | 0.9926 |
| SVR | 1,122,960 | 0.9643 |
| Linear Regression | 3,883,717 | 0.9371 |

### Traffic Classification Thresholds

| Status | Threshold |
|--------|-----------|
| Normal | < 500,000 bytes/interval |
| High | 500,000 – 50,000,000 bytes/interval |
| Congested | > 50,000,000 bytes/interval |

---

## Notes

- `sdn_topology.py` and `generate_traffic.py` each create their own Mininet instance — do **not** run them at the same time. For the demo, use the manual `sudo mn` command shown above.
- The controller appends to `traffic_data.csv` across sessions, so data accumulates over time.

---

## Author

Ahmed Shoeb
University of Trento — MSc Information Engineering
