import glob
import time
from pathlib import Path

import serial


HEAD = b"##IMG_BEGIN##"
TAIL = b"##IMG_END##"

OUTPUT_FILE = Path(__file__).resolve().parent / "capture.jpg"


def main() -> None:
    ports = glob.glob("/dev/cu.usbmodem*")

    if not ports:
        raise RuntimeError(
            "没有找到 OpenMV 串口，请检查 USB 连接。"
        )

    port = ports[0]

    print(f"找到 OpenMV 串口：{port}", flush=True)
    print("等待一张完整图片……", flush=True)

    buffer = bytearray()
    deadline = time.time() + 20

    with serial.Serial(
        port=port,
        baudrate=115200,
        timeout=0.2,
    ) as connection:
        # 丢掉打开串口前留下的半张图片，
        # 等待 OpenMV 下一张完整图片。
        connection.reset_input_buffer()

        while time.time() < deadline:
            chunk = connection.read(4096)

            if chunk:
                buffer.extend(chunk)

            start_index = buffer.find(HEAD)

            if start_index == -1:
                if len(buffer) > 100000:
                    buffer.clear()
                continue

            end_index = buffer.find(
                TAIL,
                start_index + len(HEAD),
            )

            if end_index == -1:
                continue

            image_start = start_index + len(HEAD)
            jpeg_data = bytes(
                buffer[image_start:end_index]
            )

            if not jpeg_data.startswith(b"\xff\xd8"):
                del buffer[:end_index + len(TAIL)]
                continue

            if not jpeg_data.endswith(b"\xff\xd9"):
                del buffer[:end_index + len(TAIL)]
                continue

            OUTPUT_FILE.write_bytes(jpeg_data)

            print(
                f"图片保存成功：{OUTPUT_FILE}",
                flush=True,
            )
            print(
                f"图片大小：{len(jpeg_data)} bytes",
                flush=True,
            )
            return

    raise TimeoutError(
        "20 秒内没有收到完整图片。"
    )


if __name__ == "__main__":
    main()