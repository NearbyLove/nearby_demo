# NearbyLove × CommunitySense

> 让附近，重新成为可以共同生活的地方。

NearbyLove × CommunitySense 是面向社区数智化管理的竞赛原型。它将实际居住关系、公共空间匿名感知与附近行动连接起来，帮助居民、物业、居委会和镇政府围绕具体公共问题形成可解释、可协作、可验证的改善闭环。

## 在线体验

GitHub Pages 部署成功后，从仓库右侧 **Deployments** 或 **Settings → Pages** 打开在线入口。入口页包含：

- `NearbyLove 三端协同体验`：居民、物业、居委会网页端。
- `CommunitySense 政府治理平台`：政府治理大屏。

网页使用预置 Mock 数据，不需要账号、密钥、微信开发者工具或硬件。

## 仓库结构

```text
.
├── index.html                 # GitHub Pages 在线体验入口
├── web/
│   ├── nearbylove-demo.html   # 居民、物业、居委会网页体验
│   └── communitysense-dashboard.html # 政府治理大屏
├── assets/                    # 网页所需图标与图片
├── backend/
│   └── app.py                 # Flask API 与 SQLite 数据模型
├── hardware/                  # 可选 OpenMV 串口/图片采集验证代码
├── scripts/                   # 模拟传感器读数与 API 连通性脚本
├── docs/                      # 架构、演示路径与隐私边界
└── requirements.txt           # Python 依赖
```

## 快速体验网页

无需安装依赖。克隆或下载本仓库后，在根目录运行：

```bash
python3 -m http.server 8080 --bind 127.0.0.1
```

浏览器打开 <http://127.0.0.1:8080>，再从入口页进入三端协同体验或政府治理大屏。

> 不建议直接双击 HTML 文件：政府大屏引用的浏览器资源在本地 HTTP 服务下更稳定。

## 运行后端技术验证

### 环境要求

- Python 3.11 或更高版本
- `pip`
- 可选：OpenMV 设备与可用串口，仅用于硬件验证

### 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 启动 API

```bash
python3 backend/app.py
```

API 默认运行在 <http://127.0.0.1:5000>。可用以下命令检查：

```bash
curl http://127.0.0.1:5000/api/health
```

### 写入模拟公共空间读数

另开一个终端，在后端已启动时运行：

```bash
python3 scripts/seed_demo_areas.py
curl http://127.0.0.1:5000/api/v1/areas/overview
```

`scripts/simulate_sensor.py` 会连续写入随机传感器读数。它们都是演示数据，不代表真实居民或真实场景。

## 可选 AI 配置

默认 Mock 演示不需要任何 API Key。若只为本地技术实验接入兼容 OpenAI API 的服务，可复制环境变量模板：

```bash
cp .env.example .env
```

再在本机填写 `.env`。**不得**将 `.env`、`AppSecret`、API Key、Token、真实住户数据或硬件采集图像提交到 Git。

## 隐私与演示边界

- 虚拟户口本表达实际居住关系，不是法定户籍。
- 公共空间 AI 感知不识别人脸、身份、轨迹或个体行为；它只形成待人工核实的匿名场景线索。
- AI 仅辅助摘要、引导和生成待核实线索，不自动处罚、自动上门或代替人工决定。
- 网页端所有人、房屋、行动和指标均为 Mock 数据。

详细说明见 [系统架构](docs/architecture.md)、[演示路径](docs/demo-flow.md) 和 [隐私边界](docs/privacy-boundary.md)。

## 依赖清单

Python 依赖完整列在 [`requirements.txt`](requirements.txt)，核心依赖包括：

- Flask、Flask-CORS、Flask-SQLAlchemy：本地 API 与 SQLite 数据存储。
- `openai`、`python-dotenv`：可选 AI 技术验证。
- `requests`、`pyserial`、Pillow：可选传感器/串口和图像采集验证。

静态网页没有 Node.js、npm 或构建依赖。政府治理大屏在浏览器中通过 CDN 加载 ECharts `5.5.0` 与 Leaflet `1.9.4`；首次打开该页面需要可访问这两个公开浏览器资源的网络环境。
