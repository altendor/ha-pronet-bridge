import json
import base64
import time
import websocket
import paho.mqtt.client as mqtt

OPTIONS_PATH = "/data/options.json"

ADDR_MAP = {
    "183/0/1": ("pronet/sauna/power", int),
    "183/0/2": ("pronet/sauna/set_temp", float),
    "183/0/3": ("pronet/steam/power", int),
    "183/0/4": ("pronet/steam/set_humidity", float),
    "183/0/11": ("pronet/sauna/temp_actual", float),
    "183/0/14": ("pronet/steam/humidity_actual", float),
}

def load_options():
    try:
        with open(OPTIONS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Cannot read {OPTIONS_PATH}: {repr(e)}")
        return {}

opts = load_options()
print("[DEBUG] options.json:", opts)

WS_URL = (opts.get("ws_url") or "").strip()
HTTP_USER = (opts.get("http_user") or "").strip()
HTTP_PASS = (opts.get("http_pass") or "").strip()

MQTT_HOST = (opts.get("mqtt_host") or "core-mosquitto").strip()
MQTT_USER = (opts.get("mqtt_user") or "").strip()
MQTT_PASS = (opts.get("mqtt_pass") or "").strip()

print(f"[DEBUG] mqtt_host='{MQTT_HOST}' ws_url='{WS_URL}'")

def connect_mqtt():
    if not MQTT_HOST:
        raise RuntimeError("mqtt_host is empty. Set mqtt_host to 'core-mosquitto' in add-on config.")

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
            raise RuntimeError("ws_url is empty. Please set ws_url in add-on configuration.")

        print(f"[INFO] Connecting WebSocket: {WS_URL}")
        ws = websocket.create_connection(WS_URL, header=ws_headers())
        print("[OK] WebSocket connected")

        while True:
            raw = ws.recv()
            if not raw:
                continue

            try:
                msg = json.loads(raw)
            except Exception:
                continue

            addr = msg.get("addr")
            val = msg.get("value")

            if addr in ADDR_MAP:
                topic, cast = ADDR_MAP[addr]
                try:
                    val_cast = cast(val)
                except Exception:
                    continue
                mqttc.publish(topic, str(val_cast), retain=True)

    except Exception as e:
        print(f"[ERROR] {repr(e)}")
        time.sleep(5)
