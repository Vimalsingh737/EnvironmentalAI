import json
import time
import requests
import paho.mqtt.client as mqtt


# ============================================================
# CONFIGURATION
# ============================================================

SERVER_URL = "http://10.129.7.226:5000/data"

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883

NODE_ID = "NODE_02"

LANDSLIDE_TOPIC = "environment/landslide"

INTERVAL = 5


# ============================================================
# FIXED LOCATION
# ============================================================

LATITUDE = 25.26
LONGITUDE = 86.98


# ============================================================
# MQTT CALLBACKS
# ============================================================

def on_connect(client, userdata, flags, rc):

    if rc == 0:

        print(
            "MQTT CONNECTED"
        )

    else:

        print(
            "MQTT CONNECTION FAILED:",
            rc
        )


def on_disconnect(client, userdata, rc):

    print(
        "MQTT DISCONNECTED"
    )


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(value, default=0.0):

    try:

        return float(value)

    except (TypeError, ValueError):

        return default


# ============================================================
# SAFE BOOL
# ============================================================

def safe_bool(value, default=False):

    if isinstance(value, bool):

        return value


    if isinstance(value, str):

        value = value.strip().lower()

        if value in {
            "true",
            "1",
            "yes",
            "y"
        }:

            return True


        if value in {
            "false",
            "0",
            "no",
            "n"
        }:

            return False


    if isinstance(value, (int, float)):

        return bool(value)


    return default


# ============================================================
# GET SERVER DATA
# ============================================================

def get_server_data():

    try:

        response = requests.get(
            SERVER_URL,
            timeout=5
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):

            print(
                "SERVER ERROR: Expected JSON object."
            )

            return None

        return data


    except requests.exceptions.ConnectionError:

        print(
            "WiFi server is OFF / unreachable."
        )


    except requests.exceptions.Timeout:

        print(
            "WiFi server request timed out."
        )


    except requests.exceptions.RequestException as e:

        print(
            "HTTP ERROR:",
            e
        )


    except ValueError:

        print(
            "ERROR: Server returned invalid JSON."
        )


    return None


# ============================================================
# BUILD LANDSLIDE MESSAGE
# ============================================================

def build_landslide_message(data):

    node_data = data.get(
        NODE_ID
    )


    if not isinstance(node_data, dict):

        print(
            f"{NODE_ID} landslide data not found."
        )

        return None


    return {

        "node_id": node_data.get(
            "node_id",
            NODE_ID
        ),

        "latitude": safe_float(
            node_data.get(
                "latitude",
                LATITUDE
            ),
            LATITUDE
        ),

        "longitude": safe_float(
            node_data.get(
                "longitude",
                LONGITUDE
            ),
            LONGITUDE
        ),

        "hazard": str(
            node_data.get(
                "hazard",
                "UNKNOWN"
            )
        ),

        "movement": safe_float(
            node_data.get(
                "movement",
                0
            )
        ),

        "persistent_movement": safe_bool(
            node_data.get(
                "persistent_movement",
                False
            )
        ),

        "prediction": str(
            node_data.get(
                "prediction",
                "UNKNOWN"
            )
        ),

        "rainfall": safe_float(
            node_data.get(
                "rainfall",
                0
            )
        ),

        "risk_level": str(
            node_data.get(
                "risk_level",
                "UNKNOWN"
            )
        ).upper(),

        "risk_score": safe_float(
            node_data.get(
                "risk_score",
                0
            )
        ),

        "soil_moisture": safe_float(
            node_data.get(
                "soil_moisture",
                0
            )
        )
    }


# ============================================================
# PUBLISH
# ============================================================

def publish_landslide(
    client,
    message_data
):

    message = json.dumps(
        message_data
    )


    try:

        result = client.publish(

            LANDSLIDE_TOPIC,

            message,

            qos=1
        )


        result.wait_for_publish(
            timeout=5
        )


        if result.rc == mqtt.MQTT_ERR_SUCCESS:

            print()
            print("==========================================")
            print("NODE_02 LANDSLIDE DATA SENT")
            print("==========================================")

            print(
                "Topic:",
                LANDSLIDE_TOPIC
            )

            print()

            print(
                json.dumps(
                    message_data,
                    indent=2
                )
            )

            return True


        print(
            "MQTT PUBLISH ERROR:",
            result.rc
        )


    except Exception as e:

        print(
            "MQTT PUBLISH ERROR:",
            e
        )


    return False


# ============================================================
# CONNECT MQTT
# ============================================================

def connect_mqtt(client):

    print(
        "Connecting to MQTT broker..."
    )


    while not client.is_connected():

        try:

            client.connect(
                MQTT_BROKER,
                MQTT_PORT,
                60
            )

            client.loop_start()


            for _ in range(20):

                if client.is_connected():
                    break

                time.sleep(0.1)


            if client.is_connected():

                print(
                    "Connected to MQTT broker"
                )

                return True


            print(
                "MQTT connection timed out."
            )


        except Exception as e:

            print(
                "MQTT CONNECTION ERROR:",
                e
            )

            time.sleep(3)


    return True


# ============================================================
# MAIN
# ============================================================

def main():

    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect


    connect_mqtt(
        client
    )


    print()
    print("==========================================")
    print(" NODE_02 LANDSLIDE DATA -> MQTT")
    print("==========================================")

    print(
        "Server   :",
        SERVER_URL
    )

    print(
        "Node     :",
        NODE_ID
    )

    print(
        "Topic    :",
        LANDSLIDE_TOPIC
    )

    print(
        "Broker   :",
        MQTT_BROKER
    )

    print(
        "Interval :",
        INTERVAL,
        "seconds"
    )

    print(
        "Latitude :",
        LATITUDE
    )

    print(
        "Longitude:",
        LONGITUDE
    )


    try:

        while True:

            data = get_server_data()


            if data:

                message_data = build_landslide_message(
                    data
                )


                if message_data is not None:

                    if not client.is_connected():

                        print(
                            "MQTT disconnected. Reconnecting..."
                        )

                        client.loop_stop()

                        connect_mqtt(
                            client
                        )


                    publish_landslide(
                        client,
                        message_data
                    )


            else:

                print(
                    "No data from WiFi server."
                )


            time.sleep(
                INTERVAL
            )


    except KeyboardInterrupt:

        print(
            "\nStopping landslide publisher..."
        )


    finally:

        try:

            client.loop_stop()

            client.disconnect()

        except Exception:

            pass


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()