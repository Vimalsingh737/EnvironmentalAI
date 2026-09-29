import json
import time
import requests
import paho.mqtt.client as mqtt


# ============================================================
# CONFIGURATION
# ============================================================

SERVER_URL = "http://10.64.232.226:5000/latest"

# MQTT / Mosquitto
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883

# Final fire topic
FIRE_TOPIC = "environment/fire"

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
# GET DATA FROM WIFI SERVER
# ============================================================

def get_server_data():

    try:

        response = requests.get(
            SERVER_URL,
            timeout=5
        )

        response.raise_for_status()

        response_json = response.json()

        # ----------------------------------------------------
        # Check overall response
        # ----------------------------------------------------

        if not isinstance(response_json, dict):

            print("SERVER ERROR: Expected JSON object.")

            return None

        # ----------------------------------------------------
        # Check status
        # ----------------------------------------------------

        if response_json.get("status") != "success":

            print("SERVER ERROR: status is not success.")

            return None

        # ----------------------------------------------------
        # IMPORTANT:
        # Extract ONLY the "data" section
        # ----------------------------------------------------

        data = response_json.get("data")

        if not isinstance(data, dict):

            print("SERVER ERROR: 'data' section not found.")

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
# PUBLISH FIRE DATA
# ============================================================

def publish_fire(client, data):

    # Convert ONLY data section to JSON
    message = json.dumps(data)

    try:

        result = client.publish(
            FIRE_TOPIC,
            message,
            qos=1
        )

        result.wait_for_publish(timeout=5)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:

            print()
            print("==========================================")
            print("FIRE DATA SENT")
            print("==========================================")

            print("Topic :", FIRE_TOPIC)

            print()
            print("Data sent to MQTT:")

            print(
                json.dumps(
                    data,
                    indent=2
                )
            )

            print("==========================================")

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
# CONNECT MQTT
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

            client.loop_start()

            # Give MQTT a moment to establish connection

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

            time.sleep(3)


    return True


# ============================================================
# MAIN
# ============================================================

def main():

    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    connect_mqtt(client)


    print()
    print("==========================================")
    print(" FIRE SERVER -> MQTT")
    print("==========================================")

    print("Server :", SERVER_URL)

    print("Topic  :", FIRE_TOPIC)

    print("Broker :", MQTT_BROKER)

    print("Interval:", READ_INTERVAL, "seconds")

    print()


    try:

        while True:

            # ------------------------------------------------
            # Get ONLY data section from server
            # ------------------------------------------------

            data = get_server_data()


            if data is not None:

                # --------------------------------------------
                # Make sure MQTT is connected
                # --------------------------------------------

                if not client.is_connected():

                    print(
                        "MQTT disconnected. Reconnecting..."
                    )

                    client.loop_stop()

                    connect_mqtt(client)


                # --------------------------------------------
                # Publish ONLY data section
                # --------------------------------------------

                publish_fire(
                    client,
                    data
                )


            else:

                print(
                    "No valid data from WiFi server."
                )


            time.sleep(
                READ_INTERVAL
            )


    except KeyboardInterrupt:

        print(
            "\nStopping fire publisher..."
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