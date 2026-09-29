import json
import time
import requests
import paho.mqtt.client as mqtt


# ============================================================
# CONFIGURATION
# ============================================================

# Your WiFi sensor server
SERVER_URL = "http://10.64.232.226:5000/data"

# MQTT / Mosquitto
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883

# MQTT topic
AIR_TOPIC = "environment/air"

# Air quality node ID
NODE_ID = "AIR_001"

# Read server every 5 seconds
READ_INTERVAL = 5


# ============================================================
# MQTT CALLBACKS
# ============================================================

def on_connect(client, userdata, flags, rc):

    if rc == 0:
        print("MQTT CONNECTED")

    else:
        print("MQTT CONNECTION FAILED, rc =", rc)


def on_disconnect(client, userdata, rc):

    print("MQTT DISCONNECTED")


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(value, default=0.0):

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


# ============================================================
# GET DATA FROM WIFI SERVER
# ============================================================

def get_server_data():

    try:

        print("Getting data from sensor server...")

        response = requests.get(
            SERVER_URL,
            timeout=5
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):

            print("SERVER ERROR: Expected JSON object.")

            return None

        return data

    except requests.exceptions.ConnectionError:

        print("WiFi server is OFF / unreachable.")

    except requests.exceptions.Timeout:

        print("WiFi server request timed out.")

    except requests.exceptions.RequestException as e:

        print("SERVER ERROR:", e)

    except ValueError:

        print("ERROR: Server returned invalid JSON.")

    return None


# ============================================================
# CREATE AIR QUALITY MESSAGE
# ============================================================

def build_air_message(data):

    message_data = {

        "node_id": NODE_ID,

        "dust": safe_float(
            data.get("dust", 0)
        ),

        "label": str(
            data.get("label", "Unknown")
        ),

        "mq2": safe_float(
            data.get("mq2", 0)
        ),

        "mq7": safe_float(
            data.get("mq7", 0)
        ),

        "risk": safe_float(
            data.get("risk", 0)
        )
    }

    return message_data


# ============================================================
# PUBLISH AIR DATA
# ============================================================

def publish_air(client, message_data):

    message = json.dumps(message_data)

    try:

        result = client.publish(
            AIR_TOPIC,
            message,
            qos=1
        )

        result.wait_for_publish(timeout=5)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:

            print()
            print("==========================================")
            print("AIR QUALITY DATA SENT")
            print("==========================================")

            print("Topic:", AIR_TOPIC)

            print()

            print(
                json.dumps(
                    message_data,
                    indent=2
                )
            )

            print()

            return True

        else:

            print(
                "MQTT PUBLISH ERROR:",
                result.rc
            )

    except Exception as e:

        print("MQTT PUBLISH ERROR:")
        print(e)

    return False


# ============================================================
# CONNECT TO MQTT
# ============================================================

def connect_mqtt(client):

    print("Connecting to MQTT broker...")

    while not client.is_connected():

        try:

            client.connect(
                MQTT_BROKER,
                MQTT_PORT,
                60
            )

            # Start MQTT network loop
            client.loop_start()

            # Wait for connection
            for _ in range(20):

                if client.is_connected():
                    break

                time.sleep(0.1)

            if client.is_connected():

                print("Connected to MQTT broker")

                return True

            print("MQTT connection timed out.")

        except Exception as e:

            print("MQTT CONNECTION ERROR:")
            print(e)

            print("Retrying in 3 seconds...")

            time.sleep(3)

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    # Create MQTT client
    client = mqtt.Client()

    # MQTT callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    # Connect to Mosquitto
    connect_mqtt(client)

    print()
    print("==========================================")
    print(" AIR QUALITY DATA -> MQTT")
    print("==========================================")

    print("Server   :", SERVER_URL)
    print("Node     :", NODE_ID)
    print("Topic    :", AIR_TOPIC)
    print("Broker   :", MQTT_BROKER)
    print("Interval :", READ_INTERVAL, "seconds")

    print()
    print("Publisher is running...")
    print()

    try:

        while True:

            # =================================================
            # GET DATA FROM SENSOR SERVER
            # =================================================

            data = get_server_data()

            if data:

                print("Server data received:")

                print(
                    json.dumps(
                        data,
                        indent=2
                    )
                )

                # =================================================
                # CREATE MQTT MESSAGE
                # =================================================

                message_data = build_air_message(data)

                # =================================================
                # CHECK MQTT CONNECTION
                # =================================================

                if not client.is_connected():

                    print(
                        "MQTT disconnected. Reconnecting..."
                    )

                    client.loop_stop()

                    connect_mqtt(client)

                # =================================================
                # PUBLISH TO MQTT
                # =================================================

                publish_air(
                    client,
                    message_data
                )

            else:

                print("No data from WiFi server.")

            # Wait before next request
            print(
                "Waiting",
                READ_INTERVAL,
                "seconds..."
            )

            time.sleep(
                READ_INTERVAL
            )

    except KeyboardInterrupt:

        print()
        print("Stopping air publisher...")

    finally:

        try:

            client.loop_stop()
            client.disconnect()

        except Exception:

            pass


# ============================================================
# START PROGRAM
# ============================================================

if __name__ == "__main__":

    main()