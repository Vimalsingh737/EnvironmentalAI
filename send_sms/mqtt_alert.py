import json
import os
import time

import paho.mqtt.client as mqtt
from twilio.rest import Client


# ============================================================
# MQTT CONFIGURATION
# ============================================================

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883

FIRE_TOPIC = "environment/fire"
FLOOD_TOPIC = "environment/flood"
LANDSLIDE_TOPIC = "environment/landslide"


# ============================================================
# TWILIO CONFIGURATION
# ============================================================

TWILIO_ACCOUNT_SID = os.getenv(
    "TWILIO_ACCOUNT_SID"
)

TWILIO_AUTH_TOKEN = os.getenv(
    "TWILIO_AUTH_TOKEN"
)

TWILIO_FROM = "+17372212163"

ALERT_TO = "+917860578759"


if (
    not TWILIO_ACCOUNT_SID
    or
    not TWILIO_AUTH_TOKEN
):

    raise RuntimeError(
        "TWILIO_ACCOUNT_SID and "
        "TWILIO_AUTH_TOKEN "
        "must be set."
    )


twilio_client = Client(

    TWILIO_ACCOUNT_SID,

    TWILIO_AUTH_TOKEN
)


# ============================================================
# SMS COOLDOWN
# ============================================================

# Testing
SMS_COOLDOWN = 30

# Production:
# SMS_COOLDOWN = 12 * 60 * 60


last_sms_time = {

    "FIRE": 0.0,

    "FLOOD": 0.0,

    "LANDSLIDE": 0.0
}


# ============================================================
# COOLDOWN CHECK
# ============================================================

def can_send_sms(
    alert_type
):

    current_time = time.time()

    last_time = last_sms_time.get(
        alert_type,
        0.0
    )


    if last_time == 0:

        return True


    elapsed = (
        current_time
        - last_time
    )


    remaining = (
        SMS_COOLDOWN
        - elapsed
    )


    if remaining <= 0:

        return True


    print(
        f"{alert_type} SMS cooldown active."
    )

    print(
        f"Next SMS in "
        f"{int(remaining)} seconds."
    )

    return False


# ============================================================
# SEND SMS
# ============================================================

def send_sms(
    alert_type,
    body
):

    try:

        if not can_send_sms(
            alert_type
        ):

            return


        message = (
            twilio_client
            .messages
            .create(

                body=body,

                from_=TWILIO_FROM,

                to=ALERT_TO
            )
        )


        last_sms_time[
            alert_type
        ] = time.time()


        print()
        print("==========================================")
        print("SMS SENT")
        print("==========================================")

        print(
            "Type:",
            alert_type
        )

        print(
            "SID:",
            message.sid
        )

        print(
            "Status:",
            message.status
        )

        print("==========================================")


    except Exception as e:

        print()
        print("SMS ERROR:")
        print(e)

        print(
            "Cooldown NOT started."
        )


# ============================================================
# FIRE SMS
# ============================================================

def build_fire_sms(
    data
):

    return (

        "🔥 FIRE ALERT\n"

        f"Node: "
        f"{data.get('node_id', 'UNKNOWN')}\n"

        f"Risk: "
        f"{data.get('risk_level', 'UNKNOWN')}\n"

        f"Prediction: "
        f"{data.get('prediction', 'UNKNOWN')}\n"

        f"Probability: "
        f"{data.get('fire_risk', 0)}\n"

        f"Temperature: "
        f"{data.get('temperature', 0)} C\n"

        f"Humidity: "
        f"{data.get('humidity', 0)}\n"

        f"Smoke: "
        f"{data.get('smoke_level', 0)}\n"

        f"Gas: "
        f"{data.get('gas_level', 0)}\n"

        f"Location: "
        f"{data.get('latitude', 'UNKNOWN')}, "
        f"{data.get('longitude', 'UNKNOWN')}"
    )


# ============================================================
# FLOOD SMS
# ============================================================

def build_flood_sms(
    data
):

    return (

        "🌊 FLOOD ALERT\n"

        f"Node: "
        f"{data.get('node_id', 'UNKNOWN')}\n"

        f"Risk: "
        f"{data.get('risk_level', 'UNKNOWN')}\n"

        f"Flood Risk: "
        f"{data.get('flood_risk', 0)}\n"

        f"Water Level: "
        f"{data.get('water_level', 0)} m\n"

        f"Rainfall: "
        f"{data.get('rainfall', 0)} mm\n"

        f"Temperature: "
        f"{data.get('temperature', 0)} C\n"

        f"Location: "
        f"{data.get('latitude', 'UNKNOWN')}, "
        f"{data.get('longitude', 'UNKNOWN')}"
    )


# ============================================================
# LANDSLIDE SMS
# ============================================================

def build_landslide_sms(
    data
):

    return (

        "⚠️ LANDSLIDE ALERT\n"

        f"Node: "
        f"{data.get('node_id', 'UNKNOWN')}\n"

        f"Risk: "
        f"{data.get('risk_level', 'UNKNOWN')}\n"

        f"Hazard: "
        f"{data.get('hazard', 'UNKNOWN')}\n"

        f"Prediction: "
        f"{data.get('prediction', 'UNKNOWN')}\n"

        f"Risk Score: "
        f"{data.get('risk_score', 0)}\n"

        f"Movement: "
        f"{data.get('movement', 0)}\n"

        f"Rainfall: "
        f"{data.get('rainfall', 0)} mm\n"

        f"Soil Moisture: "
        f"{data.get('soil_moisture', 0)}\n"

        f"Location: "
        f"{data.get('latitude', 'UNKNOWN')}, "
        f"{data.get('longitude', 'UNKNOWN')}"
    )


# ============================================================
# FIRE HANDLER
# ============================================================

def handle_fire(
    data
):

    prediction = str(
        data.get(
            "prediction",
            ""
        )
    ).strip().upper()


    risk_level = str(
        data.get(
            "risk_level",
            ""
        )
    ).strip().upper()


    if (

        prediction
        == "FIRE DETECTED"

        or

        risk_level
        == "HIGH"

    ):

        print(
            "FIRE ALERT CONDITION DETECTED"
        )


        send_sms(

            "FIRE",

            build_fire_sms(
                data
            )
        )


# ============================================================
# FLOOD HANDLER
# ============================================================

def handle_flood(
    data
):

    risk_level = str(
        data.get(
            "risk_level",
            ""
        )
    ).strip().upper()


    if risk_level == "HIGH":

        print(
            "FLOOD ALERT CONDITION DETECTED"
        )


        send_sms(

            "FLOOD",

            build_flood_sms(
                data
            )
        )


# ============================================================
# LANDSLIDE HANDLER
# ============================================================

def handle_landslide(
    data
):

    risk_level = str(
        data.get(
            "risk_level",
            ""
        )
    ).strip().upper()


    if risk_level in {

        "WARNING",

        "HIGH"

    }:

        print(
            "LANDSLIDE ALERT CONDITION DETECTED"
        )


        send_sms(

            "LANDSLIDE",

            build_landslide_sms(
                data
            )
        )


# ============================================================
# MQTT CONNECT
# ============================================================

def on_connect(
    client,
    userdata,
    flags,
    rc
):

    if rc == 0:

        print(
            "MQTT ALERT SERVICE CONNECTED"
        )


        client.subscribe(
            FIRE_TOPIC,
            qos=1
        )

        client.subscribe(
            FLOOD_TOPIC,
            qos=1
        )

        client.subscribe(
            LANDSLIDE_TOPIC,
            qos=1
        )


        print(
            "Subscribed to:",
            FIRE_TOPIC
        )

        print(
            "Subscribed to:",
            FLOOD_TOPIC
        )

        print(
            "Subscribed to:",
            LANDSLIDE_TOPIC
        )


    else:

        print(
            "MQTT CONNECTION FAILED:",
            rc
        )


# ============================================================
# DISCONNECT
# ============================================================

def on_disconnect(
    client,
    userdata,
    rc
):

    print(
        "MQTT ALERT SERVICE DISCONNECTED:",
        rc
    )


# ============================================================
# MQTT MESSAGE
# ============================================================

def on_message(
    client,
    userdata,
    msg
):

    try:

        data = json.loads(

            msg.payload.decode(
                "utf-8"
            )
        )


        print()
        print("------------------------------------------")

        print(
            "ALERT SERVICE RECEIVED"
        )

        print(
            "Topic:",
            msg.topic
        )

        print(
            json.dumps(
                data,
                indent=2
            )
        )

        print("------------------------------------------")


        if msg.topic == FIRE_TOPIC:

            handle_fire(
                data
            )


        elif msg.topic == FLOOD_TOPIC:

            handle_flood(
                data
            )


        elif msg.topic == LANDSLIDE_TOPIC:

            handle_landslide(
                data
            )


    except json.JSONDecodeError:

        print(
            "ERROR: Invalid JSON received."
        )


    except Exception as e:

        print(
            "ERROR PROCESSING ALERT:",
            e
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("==========================================")
    print(" ENVIRONMENTAL SMS ALERT SERVICE")
    print("==========================================")

    print(
        "Broker:",
        MQTT_BROKER
    )

    print(
        "Port:",
        MQTT_PORT
    )

    print(
        "Cooldown:",
        SMS_COOLDOWN,
        "seconds"
    )

    print()


    client = mqtt.Client()


    client.on_connect = on_connect

    client.on_disconnect = on_disconnect

    client.on_message = on_message


    client.connect(

        MQTT_BROKER,

        MQTT_PORT,

        60
    )


    client.loop_forever()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()