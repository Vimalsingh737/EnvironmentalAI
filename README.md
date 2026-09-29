EnvironmentalAI

EnvironmentalAI is an IoT-based environmental and disaster-risk
monitoring system designed to collect sensor data, process it through
Python publishers, send it using MQTT, store it in InfluxDB, and
visualize it through Grafana.

The project is designed for monitoring multiple environmental risks such
as:

🌊 Flood

🔥 Fire

⛰️ Landslide

🌫️ Air Quality

Project Architecture

Sensors / APIs
      │
      ▼
Python Data Publishers
      │
      ▼
     MQTT
  (Mosquitto)
      │
      ▼
   Telegraf
      │
      ▼
   InfluxDB
      │
      ▼
    Grafana
      │
      ├── Live Dashboard
      └── Risk Monitoring

For high-risk situations, the project can also send SMS alerts.

MQTT
 │
 ▼
mqtt_alert.py
 │
 ▼
Twilio
 │
 ▼
SMS Alert

Project Structure

EnvironmentalAI/
│
├── .venv/
│
├── ai/
│   └── area_predictor/
│       ├── fire_area_predictor.py
│       └── fire_area_model.pkl
│
├── credentials/
│   └── .env
│
├── data_fetch/
│   ├── air_publisher.py
│   ├── fire_publisher.py
│   ├── flood_publisher.py
│   └── landslide_publisher.py
│
├── send_sms/
│   ├── mqtt_alert.py
│   └── send_sms.py
│
├── telegraf/
│   └── telegraf.conf
│
└── README.md

Technologies Used

Python

MQTT

Mosquitto

Telegraf

InfluxDB

Grafana

Twilio

Machine Learning

REST APIs

VS Code

Main Components

1. Flood Publisher

data_fetch/flood_publisher.py

Fetches flood/sensor information and publishes it to:

environment/flood

Example data:

{
  "node": "FLOOD_001",
  "water_level": 4.25,
  "rainfall": 82,
  "temperature": 29.5,
  "risk_level": "HIGH"
}

2. Fire Publisher

data_fetch/fire_publisher.py

Fetches the latest fire-monitoring data and publishes only the data
object received from the API.

MQTT topic:

environment/fire

Example:

{
  "fire_probability": 0.004942,
  "fire_probability_percent": 0.49,
  "fire_status": "SAFE",
  "flame1": 0,
  "flame2": 0,
  "humidity": 83,
  "mq7": 103.3,
  "temperature": 29.8
}

3. Landslide Publisher

data_fetch/landslide_publisher.py

Publishes landslide monitoring data to:

environment/landslide

Typical fields include:

rainfall

soil moisture

movement

persistent movement

hazard

risk score

risk level

prediction

4. Air Quality Publisher

data_fetch/air_publisher.py

Publishes air-quality information to:

environment/air

Typical values include:

{
  "dust": 46.54,
  "label": "Moderate",
  "mq2": 1.5,
  "mq7": 0.71,
  "risk": 0.00064
}

MQTT Topics

Data Type     MQTT Topic

Flood         environment/flood
Fire          environment/fire
Landslide     environment/landslide
Air Quality   environment/air

The local Mosquitto broker normally runs on:

127.0.0.1:1883

Data Pipeline

Step 1 --- Data Collection

Python publishers obtain data from sensors or REST APIs.

Step 2 --- MQTT

The publishers send JSON data to Mosquitto.

Example:

Python → MQTT → environment/fire

Step 3 --- Telegraf

Telegraf subscribes to the MQTT topics and converts the incoming JSON
data into InfluxDB measurements.

Step 4 --- InfluxDB

InfluxDB stores the time-series environmental data.

Recommended configuration:

Organization: EnvironmentalAI
Bucket: environment_data
URL: http://localhost:8086

Step 5 --- Grafana

Grafana reads data from InfluxDB and displays live environmental
information through dashboards.

Possible dashboard cards:

FLOOD        FIRE        LANDSLIDE        AIR QUALITY
LIVE         SAFE        LOW              MODERATE

SMS Alert System

The project contains:

send_sms/mqtt_alert.py

The alert service listens to MQTT messages and can send an SMS when a
configured risk condition is reached.

For example:

Risk Level = HIGH
       ↓
MQTT Alert Listener
       ↓
Twilio
       ↓
SMS Alert

Twilio credentials should be stored in environment variables and should
never be committed to GitHub.

Example:

TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token

Installation

1. Clone the repository

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd EnvironmentalAI

2. Create a virtual environment

Windows PowerShell:

python -m venv .venv

Activate it:

.\.venv\Scripts\Activate.ps1

3. Install Python dependencies

If a requirements.txt file is available:

pip install -r requirements.txt

Otherwise install the required packages used by the individual
publishers and services.

Required Services

The local system requires:

Mosquitto

MQTT broker:

127.0.0.1:1883

InfluxDB

Open:

http://localhost:8086

Telegraf

Telegraf reads MQTT messages using:

telegraf/telegraf.conf

Make sure the configuration contains an output plugin pointing to
InfluxDB.

Grafana

Grafana should use InfluxDB as its data source.

Running the Project

Start the services in approximately this order:

1. Mosquitto
2. InfluxDB
3. Telegraf
4. Python publishers
5. Grafana
6. SMS listener (optional)

Example Python commands:

python data_fetch/fire_publisher.py

python data_fetch/flood_publisher.py

python data_fetch/landslide_publisher.py

python data_fetch/air_publisher.py

Run the SMS listener when required:

python send_sms/mqtt_alert.py

Telegraf Configuration

The Telegraf configuration subscribes to MQTT topics such as:

[[inputs.mqtt_consumer]]
  servers = ["tcp://127.0.0.1:1883"]
  topics = ["environment/fire"]
  qos = 1
  data_format = "json_v2"

Multiple MQTT input sections can be used for the different environmental
data streams.

The configuration must also contain an InfluxDB output. Without an
output plugin, Telegraf can report:

no outputs found

Security

Do not commit:

.env
credentials
Twilio authentication tokens
InfluxDB API tokens
private keys
passwords

Add sensitive files to .gitignore.

Example:

.venv/
.env
credentials/.env
__pycache__/
*.pyc

Future Improvements

Raspberry Pi sensor nodes

LoRa communication

Multiple geographical sensor nodes

India-wide disaster monitoring map

Real-time risk classification

AI-based prediction

Automatic high-risk SMS alerts

Public cloud deployment

Historical disaster analysis

Geofenced emergency notifications

More advanced Grafana dashboards

Goal

The long-term goal of EnvironmentalAI is to create a real-time
environmental intelligence network that combines IoT sensors, machine
learning, MQTT, time-series data storage, visualization, and emergency
notification systems for disaster-risk monitoring.

Author

Vimal Kumar Singh

B.Tech CSE
Indian Institute of Information Technology Bhagalpur

GitHub: Vimalsingh737