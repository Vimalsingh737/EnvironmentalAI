import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import paho.mqtt.client as mqtt


# ============================================================
# CONFIGURATION
# ============================================================

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883

# FINAL FIRE INPUT
INPUT_TOPIC = "environment/fire"

# Fire area prediction output
OUTPUT_TOPIC = "environment/fire_prediction"

# Model is in the same folder as this Python file
MODEL_PATH = (
    Path(__file__).resolve().parent
    / "fire_area_model.pkl"
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
# LOAD MODEL
# ============================================================

print(
    "Loading fire area prediction model..."
)

print(
    "Model path:",
    MODEL_PATH
)


if not MODEL_PATH.exists():

    raise FileNotFoundError(
        f"Model file not found: {MODEL_PATH}"
    )


model = joblib.load(
    MODEL_PATH
)


print(
    "Model loaded successfully."
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
            "Connected to MQTT broker."
        )

        client.subscribe(
            INPUT_TOPIC,
            qos=1
        )

        print(
            f"Subscribed to: {INPUT_TOPIC}"
        )

    else:

        print(
            "MQTT connection failed:",
            rc
        )


# ============================================================
# MQTT DISCONNECT
# ============================================================

def on_disconnect(
    client,
    userdata,
    rc
):

    print(
        "MQTT DISCONNECTED:",
        rc
    )


# ============================================================
# MESSAGE CALLBACK
# ============================================================

def on_message(
    client,
    userdata,
    msg
):

    try:

        # ----------------------------------------------------
        # READ MESSAGE
        # ----------------------------------------------------

        payload = msg.payload.decode(
            "utf-8"
        )

        data = json.loads(
            payload
        )


        print()
        print("==========================================")
        print("Received fire data")
        print("==========================================")

        print(
            json.dumps(
                data,
                indent=2
            )
        )


        # ----------------------------------------------------
        # EXTRACT DATA
        # ----------------------------------------------------

        node_id = data.get(
            "node_id",
            "UNKNOWN"
        )


        latitude = safe_float(
            data.get(
                "latitude",
                0
            )
        )


        longitude = safe_float(
            data.get(
                "longitude",
                0
            )
        )


        temperature = safe_float(
            data.get(
                "temperature",
                0
            )
        )


        humidity = safe_float(
            data.get(
                "humidity",
                0
            )
        )


        smoke_level = safe_float(
            data.get(
                "smoke_level",
                data.get(
                    "smoke",
                    0
                )
            )
        )


        gas_level = safe_float(
            data.get(
                "gas_level",
                data.get(
                    "gas",
                    0
                )
            )
        )


        risk_probability = safe_float(
            data.get(
                "fire_risk",
                data.get(
                    "probability",
                    0
                )
            )
        )


        prediction = str(
            data.get(
                "prediction",
                "NORMAL"
            )
        ).strip()


        risk_level = str(
            data.get(
                "risk_level",
                ""
            )
        ).strip().upper()


        if not risk_level:

            if (
                prediction.upper()
                == "FIRE DETECTED"
            ):

                risk_level = "HIGH"

            else:

                risk_level = "LOW"


        # ----------------------------------------------------
        # CREATE MODEL INPUT
        # ----------------------------------------------------
        #
        # YOUR CURRENT MODEL WAS DESIGNED WITH
        # THESE 4 FEATURES:
        #
        # smoke_level
        # temperature
        # humidity
        # risk_probability
        #
        # Keep them exactly consistent with training.
        # ----------------------------------------------------

        features = pd.DataFrame([
            {

                "smoke_level":
                    smoke_level,

                "temperature":
                    temperature,

                "humidity":
                    humidity,

                "risk_probability":
                    risk_probability
            }
        ])


        print()
        print(
            "Model input:"
        )

        print(features)


        # ----------------------------------------------------
        # FIRE AREA PREDICTION
        # ----------------------------------------------------

        if (
            prediction.upper()
            == "FIRE DETECTED"
            or
            risk_level
            == "HIGH"
        ):

            prediction_log = model.predict(
                features
            )[0]


            # IMPORTANT:
            # This assumes your model was trained on
            # log1p(area_hectares).
            predicted_area_hectares = float(
                np.expm1(
                    prediction_log
                )
            )


            predicted_area_hectares = max(
                0.0,
                predicted_area_hectares
            )


            predicted_area_hectares = round(
                predicted_area_hectares,
                2
            )


            # 1 km² = 100 hectares
            predicted_area_km2 = round(
                predicted_area_hectares
                / 100.0,
                4
            )


        else:

            predicted_area_hectares = 0.0

            predicted_area_km2 = 0.0


        # ----------------------------------------------------
        # CREATE RESULT
        # ----------------------------------------------------

        result = {

            "node_id":
                node_id,

            "latitude":
                latitude,

            "longitude":
                longitude,

            "temperature":
                temperature,

            "smoke_level":
                smoke_level,

            "gas_level":
                gas_level,

            "humidity":
                humidity,

            "risk_probability":
                risk_probability,

            "risk_level":
                risk_level,

            "prediction":
                prediction,

            "predicted_area_hectares":
                predicted_area_hectares,

            "predicted_area_km2":
                predicted_area_km2
        }


        # ----------------------------------------------------
        # PUBLISH
        # ----------------------------------------------------

        output = json.dumps(
            result
        )


        info = client.publish(

            OUTPUT_TOPIC,

            output,

            qos=1
        )


        info.wait_for_publish(
            timeout=5
        )


        # ----------------------------------------------------
        # PRINT
        # ----------------------------------------------------

        print()
        print("==========================================")
        print("FIRE AREA PREDICTION")
        print("==========================================")

        print(
            output
        )

        print(
            "Published to:",
            OUTPUT_TOPIC
        )

        print(
            "Publish status:",
            info.rc
        )


    except json.JSONDecodeError:

        print(
            "ERROR: Invalid JSON received."
        )


    except Exception as e:

        print()
        print("==========================================")
        print("ERROR PROCESSING FIRE MESSAGE")
        print("==========================================")

        print(e)


# ============================================================
# MQTT CLIENT
# ============================================================

client = mqtt.Client()

client.on_connect = on_connect

client.on_disconnect = on_disconnect

client.on_message = on_message


# ============================================================
# CONNECT
# ============================================================

print()
print("==========================================")
print(" FIRE AREA PREDICTION SERVICE")
print("==========================================")

print(
    "Input topic :",
    INPUT_TOPIC
)

print(
    "Output topic:",
    OUTPUT_TOPIC
)

print(
    "Model       :",
    MODEL_PATH
)

print()


client.connect(

    MQTT_BROKER,

    MQTT_PORT,

    60
)


# ============================================================
# START
# ============================================================

client.loop_forever()