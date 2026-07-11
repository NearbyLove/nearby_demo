import socket

server = socket.socket()
# 端口复用，避免8888占用报错
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", 8888))
server.listen(1)
print("等待ESP连接，端口8888")

while True:
    conn, addr = server.accept()
    print("ESP已接入：", addr)
    buffer = b""
    # 持续接收直到ESP断开连接
    while True:
        data = conn.recv(1024)
        if not data:
            break
        buffer += data
        print("收到数据长度：", len(buffer))
    # 连接断开后一次性保存完整图片
    if len(buffer) > 1000:
        with open("capture.jpg", "wb") as f:
            f.write(buffer)
        print("图片保存完成 capture.jpg")
    conn.close()