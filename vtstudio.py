import websocket
import json
import uuid
import time
import random

VTS_URL = "ws://127.0.0.1:8001"

PLUGIN_NAME = "AI Avatar Controller"
PLUGIN_DEVELOPER = "Fedor"

# ─────────────────────────────────────────────
# Avatar Controller
# ─────────────────────────────────────────────

class VTubeAvatar:
    def __init__(self, token: str | None = None):
        self.ws = websocket.WebSocket()
        self.ws.connect(VTS_URL)
        self.token = token

        if not self.token:
            self.token = self.request_token()
            print("\n🔑 SAVE THIS TOKEN:")
            print(self.token)
            print("────────────────────\n")

        self.authenticate()

    # ───────── API utils ─────────

    def send(self, message: dict):
        self.ws.send(json.dumps(message))
        return json.loads(self.ws.recv())

    def request_token(self) -> str:
        req = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": str(uuid.uuid4()),
            "messageType": "AuthenticationTokenRequest",
            "data": {
                "pluginName": PLUGIN_NAME,
                "pluginDeveloper": PLUGIN_DEVELOPER,
                "pluginIcon": ""
            }
        }
        res = self.send(req)
        return res["data"]["authenticationToken"]

    def authenticate(self):
        req = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "auth",
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": PLUGIN_NAME,
                "pluginDeveloper": PLUGIN_DEVELOPER,
                "authenticationToken": self.token
            }
        }
        res = self.send(req)
        if not res["data"]["authenticated"]:
            raise RuntimeError("❌ Auth failed")
        print("✅ Connected to VTube Studio")
   # ───────── Parameter control ─────────

    def set_params(self, params: dict):
        req = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": str(uuid.uuid4()),
            "messageType": "InjectParameterDataRequest",
            "data": {
                "mode": "add",
                "parameterValues": [
                    {"id": k, "value": v}
                    for k, v in params.items()
                ]
            }
        }
        self.send(req)

    # ───────── Animations ─────────

    def blink(self):
        self.set_params({
            "ParamEyeBlinkLeft": 1.0,
            "ParamEyeBlinkRight": 1.0
        })
        time.sleep(0.1)
        self.set_params({
            "ParamEyeBlinkLeft": 0.0,
            "ParamEyeBlinkRight": 0.0
        })

    def smile(self, value=1.0):
        self.set_params({"ParamMouthSmile": value})

    def neutral(self):
        self.set_params({"ParamMouthSmile": 0.0})

    def head_idle(self):
        self.set_params({
            "ParamAngleX": random.uniform(-5, 5),
            "ParamAngleY": random.uniform(-5, 5),
            "ParamAngleZ": random.uniform(-3, 3)
        })

    def emotion(self, name: str):
        match name:
            case "happy":
                self.smile(1.0)
            case "sad":
                self.set_params({"ParamMouthSmile": -0.7})
            case "angry":
                self.set_params({"ParamBrowAngry": 1.0})
            case _:
                self.neutral()
# ───────── Cleanup ─────────

    def close(self):
        self.ws.close()


# ─────────────────────────────────────────────
# DEMO LOOP
# ─────────────────────────────────────────────

if __name__ == "__main__":
    """
    1️⃣ Первый запуск — БЕЗ токена
    2️⃣ Разреши доступ в VTube Studio
    3️⃣ Скопируй токен в код
    """

    avatar = VTubeAvatar(
        token='bdb903c8105885c39bc51982ba4e3261ef7367b50211fe27651af7e133c23b04'  # ← вставь токен сюда после первого запуска
    )

    try:
        while True:
            avatar.head_idle()

            if random.random() < 0.2:
                avatar.blink()

            if random.random() < 0.3:
                avatar.emotion(random.choice(["happy", "neutral", "sad"]))

            time.sleep(1.0)

    except KeyboardInterrupt:
        avatar.close()
        print("👋 Disconnected")