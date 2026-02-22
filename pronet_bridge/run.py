import os
import json
import base64
import time
import websocket
import paho.mqtt.client as mqtt

WS_URL = os.environ.get("WS_URL")
HTTP_USER = os.environ.get("HTTP_USER")
HTTP_PASS = os.environ.get("HTTP_PASS")

MQTT_HOST = os.environ.get("MQTT_HOST")
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASS = os.environ.get("MQTT_PASS")

ADDR_MAP = {
    "183/0/1": ("pronet/sauna/power", int),
    "183/0/2": ("pronet/sauna/set_temp", float),
    "183/0/3": ("pronet/steam/power", int),
    "183/0/4": ("pronet/steam/set_humidity", float),
    "183/0/11": ("pronet/sauna/temp_actual", float),
    "183/0/14": ("pronet/steam/humidity_actual", float),
}

def connect_mqtt():
    client = mqtt.Client()
    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.connect(MQTT_HOST, 1883, 60)
    client.loop_start()
    return client

def ws_headers():
    if HTTP_USER:
        token = base64.b64encode(f"{HTTP_USER}:{HTTP_PASS}".encode()).decode()
        return [f"Authorization: Basic {token}"]
    return []

mqttc = connect_mqtt()

while True:
    try:
        ws = websocket.create_connection(WS_URL, header=ws_headers())
        while True:
            raw = ws.recv()
            msg = json.loads(raw)

            addr = msg.get("addr")
            val = msg.get("value")

            if addr in ADDR_MAP:
                topic, cast = ADDR_MAP[addr]
                try:
                    val = cast(val)
                except:
                    continue
                mqttc.publish(topic, str(val), retain=True)

    except Exception:
        time.sleep(5)
