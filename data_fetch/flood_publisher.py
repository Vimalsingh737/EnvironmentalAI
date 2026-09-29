import requests
import json
import time
import paho.mqtt.client as mqtt


# -----------------------------
# Configuration
# -----------------------------

SENSOR_URL = "http://10.64.232.226:5000/sensor"

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "environment/flood"

NODE_ID = "FLOOD_001"

FETCH_INTERVAL = 5


# -----------------------------
# MQTT setup
# -----------------------------

client = mqtt.Client()

client.connect(MQTT_BROKER, MQTT_PORT, 60)

print("Connected to Mosquitto")
print("Starting flood sensor publisher...")


# -----------------------------
# Main loop
# -----------------------------

while True:

    try:

        # Get data from sensor API
        response = requests.get(SENSOR_URL, timeout=5)

        response.raise_for_status()

        sensor_data = response.json()

        print("\nSensor data received:")
        print(sensor_data)


        # Create MQTT message
        mqtt_data = {
            "node_id": NODE_ID,

            "risk_score": sensor_data.get("risk_score", 0),

            "risk_type": sensor_data.get(
                "risk_type",
                "NORMAL"
            ),

            "water_depth_cm": sensor_data.get(
                "water_depth_cm",
                0
            ),

            "water_flow_ml_min": sensor_data.get(
                "water_flow_ml_min",
                0
            )
        }


        # Convert Python dictionary to JSON
        message = json.dumps(mqtt_data)


        # Publish to MQTT
        client.publish(
            MQTT_TOPIC,
            message
        )


        print("Published to MQTT:")
        print(message)


    except requests.exceptions.RequestException as e:

        print("Sensor API error:", e)


    except Exception as e:

        print("Error:", e)


    time.sleep(FETCH_INTERVAL)