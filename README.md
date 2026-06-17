Machine Learning-Based Network Traffic Prediction in SDN
A closed-loop system where a Software-Defined Networking (SDN) controller monitors its own network traffic, trains machine learning models on the collected data, and classifies live traffic as Normal, High, or Congested in real time.
Course: Networking — Module 2 Project

Institution: University of Trento — MSc Information Engineering

Overview
Traditional networks are reactive — they respond to congestion only after packets are already lost. This project makes the network proactive by combining:

SDN (Software-Defined Networking): a Ryu controller centrally monitors all switches
Machine Learning: four models are trained to predict and classify traffic load

The Ryu controller collects port statistics every 5 seconds, logs them to a CSV file, and a machine learning pipeline trains on this data to classify network state in real time.

<img width="630" height="330" alt="topology" src="https://github.com/user-attachments/assets/1b00751a-50ac-4b5e-a552-5e3a0ea75c02" />

2 hosts (h1, h2) generate traffic
2 OpenFlow switches (s1, s2) forward packets
Ryu controller collects statistics every 5 seconds
(ML pipeline classifies traffic in real time)


Requirements

ComNetsEmu virtual machine (includes Mininet, Ryu, Open vSwitch)
Python 3 with the following libraries:

pandas
numpy
scikit-learn
matplotlib



Install the Python libraries if needed:
bashpip3 install pandas numpy scikit-learn matplotlib

File Structure
FilePurposeryu_csv_logger.pyRyu controller — collects traffic statistics and logs to CSVsdn_topology.pyBuilds the Mininet network (2 hosts, 2 switches)generate_traffic.pyGenerates ICMP and TCP traffic between hoststrain_svm_model.pyTrains and compares 4 ML modelsreal_time_predict.pyLive traffic prediction and classificationanalyze_traffic.pyPlots traffic graphs and basic analysismodel_comparison_results.csvSaved model comparison resultstraffic_data.csvPre-collected dataset (ready to use immediately)

Step-by-Step Installation and Run Guide
The demo uses 4 terminals. Open them inside the ComNetsEmu VM and navigate to the project folder in each:
bashcd ~/comnetsemu/examples/traffic_prediction_final
Step 0 — Clean any previous sessions
bashsudo mn -c
sudo pkill -f ryu
Step 1 — Terminal 1: Start the Ryu Controller
bashsudo ryu-manager ryu_csv_logger.py ryu.app.simple_switch_13 --ofp-tcp-listen-port 6633
Wait until you see the line ending with OFPHandler. The controller is now running. Leave this terminal open.
Step 2 — Terminal 2: Start the Network
bashsudo mn --controller=remote,ip=127.0.0.1,port=6633 --switch=ovsk,protocols=OpenFlow13 --topo=linear,2 --mac
When the mininet> prompt appears, test connectivity:
mininet> h1 ping -c 3 10.0.0.2
You should see 0% packet loss, confirming the network is working.
Step 3 — Terminal 3: Watch Data Collection (optional)
bashwatch -n 2 wc -l traffic_data.csv
This shows the CSV growing as the controller logs traffic.
Step 4 — Terminal 2: Generate Traffic
Generate traffic at realistic rates (run each line one after another):
mininet> h2 iperf -s &
mininet> h1 iperf -c 10.0.0.2 -t 30 -b 1M
mininet> h1 iperf -c 10.0.0.2 -t 30 -b 5M
mininet> h1 iperf -c 10.0.0.2 -t 30 -b 100M
mininet> h1 iperf -c 10.0.0.2 -t 30 -b 500M
These bandwidth values simulate real-world scenarios:

1M — light browsing
5M — HD streaming
100M — heavy download
500M — network congestion

Step 5 — Terminal 4: Train the Models
bashpython3 train_svm_model.py
This trains 4 models and prints a comparison table, then saves results to model_comparison_results.csv.
Step 6 — Terminal 4: Run Live Prediction
bashpython3 real_time_predict.py
This watches for new traffic and classifies it live. Generate more traffic in Terminal 2 to see the status change between Normal, High, and Congested.
Step 7 — Shutdown
mininet> exit          (in Terminal 2)
Ctrl + C               (in Terminal 4, then Terminal 1)
sudo mn -c             (final cleanup)

Machine Learning Approach
Target: rx_rate — delta bytes per 5-second interval (actual throughput, not cumulative counters)
Features:

rx_rate_lag1, tx_rate_lag1 — previous interval values (temporal context)
tx_rate, port, datapath

Key techniques:

Management port filtering — port 4294967294 (OFPP_LOCAL) removed at source and in preprocessing
Log transform — np.log1p compresses the large value range so SVR works correctly
70/30 train-test split with StandardScaler normalization

Model Comparison Results
ModelMAE (bytes)R²Decision Tree86,4890.9934Random Forest99,0230.9926SVR1,122,9600.9643Linear Regression3,883,7170.9371
Traffic Classification Thresholds
StatusThresholdNormal< 500,000 bytes/intervalHigh500,000 – 50,000,000 bytes/intervalCongested> 50,000,000 bytes/interval

Notes

A pre-collected dataset (traffic_data.csv) is included so the demo can be run immediately without waiting to generate new data. The Ryu controller will append new traffic to this same file if you choose to collect more.
sdn_topology.py and generate_traffic.py each create their own Mininet instance — do not run them at the same time. For the demo, use the manual sudo mn command shown above.


Author
Ahmed Shoeb

University of Trento — MSc Information Engineering
