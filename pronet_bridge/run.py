import json
import base64
import time
import websocket
import paho.mqtt.client as mqtt

OPTIONS_PATH = "/data/options.json"

def load_options():
    with open(OPTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

opts = load_options()

WS_URL = opts.get("ws_url")
HTTP_USER = opts.get("http_user", "")
HTTP_PASS = opts.get("http_pass", "")

MQTT_HOST = opts.get("mqtt_host", "core-mosquitto")
MQTT_USER = opts.get("mqtt_user", "")
MQTT_PASS = opts.get("mqtt_pass", "")

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
    print(f"[OK] MQTT connected to {MQTT_HOST}:1883")
    return client

def ws_headers():
    if HTTP_USER:
        token = base64.b64encode(f"{HTTP_USER}:{HTTP_PASS}".encode()).decode()
        return [f"Authorization: Basic {token}"]
    return []

mqttc = connect_mqtt()

while True:
    try:
        if not WS_URL:
            raise RuntimeError("ws_url is empty. Please set it in the add-on configuration.")

        print(f"[INFO] Connecting WS: {WS_URL}")
        ws = websocket.create_connection(WS_URL, header=ws_headers())
        print("[OK] WS connected")

        while True:
            raw = ws.recv()
            msg = json.loads(raw)

            addr = msg.get("addr")
            val = msg.get("value")

            if addr in ADDR_MAP:
                topic, cast = ADDR_MAP[addr]
                try:
                    val = cast(val)
                except Exception:
                    continue
                mqttc.publish(topic, str(val), retain=True)

    except Exception as e:
        print(f"[ERR] {repr(e)}")
        time.sleep(5)
