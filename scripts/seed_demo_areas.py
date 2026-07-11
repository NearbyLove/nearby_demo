import json
import random
import urllib.error
import urllib.request
from datetime import datetime, timezone

API_URL = "http://127.0.0.1:5000/api/v1/sensor-readings"

AREA_PROFILES = {
    "garden_A": {
        "motion_range": (5.5, 8.5),
        "brightness_range": (55, 85),
    },
    "entrance_B": {
        "motion_range": (3.0, 5.5),
        "brightness_range": (45, 75),
    },
    "corridor_C": {
        "motion_range": (0.3, 2.0),
        "brightness_range": (8, 18),
    },
}


def build_payload(
    area_id: str,
    motion_range: tuple[float, float],
    brightness_range: tuple[float, float],
) -> dict:
    return {
        "protocol_version": "1.0",
        "device_id": f"openmv-{area_id.lower()}-01",
        "area_id": area_id,
        "captured_at": datetime.now(
            timezone.utc
        ).astimezone().isoformat(timespec="seconds"),
        "metrics": {
            "motion_score": round(
                random.uniform(*motion_range),
                2,
            ),
            "brightness": round(
                random.uniform(*brightness_range),
                2,
            ),
            "fps": round(random.uniform(15, 24), 2),
        },
        "status": {
            "rssi": random.randint(-72, -42),
            "uptime_s": random.randint(100, 5000),
        },
    }


def send_payload(payload: dict) -> None:
    request_body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=5,
        ) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        print(
            payload["area_id"],
            payload["metrics"]["motion_score"],
            payload["metrics"]["brightness"],
            result["message"],
        )

    except urllib.error.URLError as exc:
        print("Request failed:", exc)


if __name__ == "__main__":
    for area_id, profile in AREA_PROFILES.items():
        for _ in range(10):
            payload = build_payload(
                area_id=area_id,
                motion_range=profile["motion_range"],
                brightness_range=profile[
                    "brightness_range"
                ],
            )
            send_payload(payload)