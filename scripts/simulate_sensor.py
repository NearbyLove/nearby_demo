import json
import random
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

API_URL = "http://127.0.0.1:5000/api/v1/sensor-readings"

DEVICE_ID = "openmv-garden-01"
AREA_ID = "garden_A"


def generate_payload() -> dict:
    return {
        "protocol_version": "1.0",
        "device_id": DEVICE_ID,
        "area_id": AREA_ID,
        "captured_at": datetime.now(
            timezone.utc
        ).astimezone().isoformat(timespec="seconds"),
        "metrics": {
            "motion_score": round(random.uniform(0, 10), 2),
            "brightness": round(random.uniform(35, 90), 2),
            "fps": round(random.uniform(15, 25), 2),
        },
        "status": {
            "rssi": random.randint(-75, -40),
            "uptime_s": int(time.monotonic()),
        },
    }


def send_payload(payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))

        print(
            "Sent:",
            payload["metrics"]["motion_score"],
            result["message"],
        )

    except urllib.error.URLError as exc:
        print("Request failed:", exc)


if __name__ == "__main__":
    for _ in range(15):
        send_payload(generate_payload())
        time.sleep(2)