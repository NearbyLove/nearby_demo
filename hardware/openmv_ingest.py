import glob
import io
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
import serial
from PIL import Image


HEAD = b"##IMG_BEGIN##"
TAIL = b"##IMG_END##"

DEVICE_ID = "openmv_usb_01"
AREA_ID = "corridor_C"

BACKEND_URL = (
    "http://127.0.0.1:5000"
    "/api/v1/sensor-readings"
)

EVALUATE_URL = (
    "http://127.0.0.1:5000"
    f"/api/v1/areas/{AREA_ID}/evaluate"
)

OUTPUT_FILE = (
    Path(__file__).resolve().parent
    / "capture.jpg"
)

POST_INTERVAL_SECONDS = 5


def find_openmv_port() -> str:
    ports = glob.glob("/dev/cu.usbmodem*")

    if not ports:
        raise RuntimeError(
            "没有找到 OpenMV 串口，请检查 USB 连接。"
        )

    return ports[0]


def calculate_brightness(jpeg_data: bytes) -> float:
    """
    将图片平均灰度从 0～255 换算为后端统一的 0～100。
    原始图片只在本机内存中处理。
    """
    with Image.open(io.BytesIO(jpeg_data)) as image:
        grayscale = image.convert("L")
        histogram = grayscale.histogram()

    pixel_count = sum(histogram)

    if pixel_count == 0:
        return 0.0

    brightness_sum = sum(
        value * count
        for value, count in enumerate(histogram)
    )

    raw_brightness = brightness_sum / pixel_count

    return raw_brightness / 255.0 * 100.0


def send_to_backend(brightness: float) -> None:
    payload = {
        "protocol_version": "1.0",
        "device_id": DEVICE_ID,
        "area_id": AREA_ID,
        "captured_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "metrics": {
            "brightness": round(brightness, 2),
            "motion_score": 0.0,
            "fps": 0.5,
        },
        "status": {
            "source": "openmv_usb",
            "raw_image_uploaded": False,
        },
    }

    try:
        response = requests.post(
            BACKEND_URL,
            json=payload,
            timeout=5,
        )

        print(
            f"后端响应：{response.status_code} "
            f"{response.text[:300]}"
        )

        if response.ok:
            evaluation_response = requests.post(
                EVALUATE_URL,
                timeout=5,
            )

            print(
                "区域评估响应："
                f"{evaluation_response.status_code} "
                f"{evaluation_response.text[:300]}"
            )

    except requests.RequestException as error:
        print(f"后端连接失败：{error}")


def extract_frame(
    buffer: bytearray,
) -> Optional[bytes]:
    start_index = buffer.find(HEAD)

    if start_index == -1:
        if len(buffer) > 200000:
            buffer.clear()

        return None

    end_index = buffer.find(
        TAIL,
        start_index + len(HEAD),
    )

    if end_index == -1:
        if start_index > 0:
            del buffer[:start_index]

        return None

    image_start = start_index + len(HEAD)

    jpeg_data = bytes(
        buffer[image_start:end_index]
    )

    del buffer[:end_index + len(TAIL)]

    if not jpeg_data.startswith(b"\xff\xd8"):
        return None

    if not jpeg_data.endswith(b"\xff\xd9"):
        return None

    return jpeg_data


def main() -> None:
    port = find_openmv_port()

    print(f"找到 OpenMV：{port}")
    print("开始接收图片并计算亮度……")

    buffer = bytearray()
    last_post_time = 0.0

    with serial.Serial(
        port=port,
        baudrate=115200,
        timeout=0.2,
    ) as connection:
        connection.reset_input_buffer()

        while True:
            chunk = connection.read(4096)

            if not chunk:
                continue

            buffer.extend(chunk)

            jpeg_data = extract_frame(buffer)

            if jpeg_data is None:
                continue

            OUTPUT_FILE.write_bytes(jpeg_data)

            brightness = calculate_brightness(
                jpeg_data
            )

            print(
                f"收到图片：{len(jpeg_data)} bytes，"
                f"平均亮度：{brightness:.2f}"
            )

            current_time = time.time()

            if (
                current_time - last_post_time
                >= POST_INTERVAL_SECONDS
            ):
                send_to_backend(brightness)
                last_post_time = current_time


if __name__ == "__main__":
    main()