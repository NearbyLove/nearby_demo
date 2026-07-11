from datetime import datetime
from typing import Any, Dict

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

import json
import os
import re
import uuid
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv(override=True)

app = Flask(__name__)
app.json.ensure_ascii = False

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///communitysense.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app)
db = SQLAlchemy(app)


class SensorReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    protocol_version = db.Column(db.String(16), nullable=False)
    device_id = db.Column(db.String(64), nullable=False, index=True)
    area_id = db.Column(db.String(64), nullable=False, index=True)
    captured_at = db.Column(db.String(40), nullable=False)

    motion_score = db.Column(db.Float, nullable=False)
    brightness = db.Column(db.Float, nullable=True)
    fps = db.Column(db.Float, nullable=True)

    rssi = db.Column(db.Integer, nullable=True)
    uptime_s = db.Column(db.Integer, nullable=True)

    received_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "protocol_version": self.protocol_version,
            "device_id": self.device_id,
            "area_id": self.area_id,
            "captured_at": self.captured_at,
            "metrics": {
                "motion_score": self.motion_score,
                "brightness": self.brightness,
                "fps": self.fps,
            },
            "status": {
                "rssi": self.rssi,
                "uptime_s": self.uptime_s,
            },
            "received_at": self.received_at.isoformat(),
        }

class AreaEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    area_id = db.Column(db.String(64), nullable=False, index=True)
    event_type = db.Column(db.String(64), nullable=False)
    severity = db.Column(db.String(32), nullable=False)

    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(500), nullable=False)

    status = db.Column(
        db.String(32),
        nullable=False,
        default="pending",
    )

    source = db.Column(
        db.String(32),
        nullable=False,
        default="edge_sensor",
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    def to_dict(self) -> Dict[str, Any]:
      event_date = (
          self.created_at.strftime("%Y%m%d")
          if self.created_at
          else "UNKNOWN"
      )

      event_code = (
          f"CS-{event_date}-{self.id:04d}"
          if self.id is not None
          else None
      )

      return {
          "id": self.id,
          "event_code": event_code,
          "area_id": self.area_id,
          "event_type": self.event_type,
          "severity": self.severity,
          "title": self.title,
          "message": self.message,
          "status": self.status,
          "source": self.source,
          "created_at": self.created_at.isoformat(),
      }

class EventTransition(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    event_id = db.Column(
        db.Integer,
        db.ForeignKey("area_event.id"),
        nullable=False,
        index=True,
    )

    from_status = db.Column(db.String(32), nullable=False)
    to_status = db.Column(db.String(32), nullable=False)

    actor_role = db.Column(db.String(32), nullable=False)
    actor_name = db.Column(db.String(100), nullable=False)

    note = db.Column(db.String(500), nullable=True)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_id": self.event_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "actor_role": self.actor_role,
            "actor_name": self.actor_name,
            "note": self.note,
            "created_at": self.created_at.isoformat(),
        }

class CareTask(db.Model):
    __tablename__ = "care_tasks"

    id = db.Column(db.String(64), primary_key=True)

    service_type = db.Column(
        db.String(100),
        nullable=False,
        default="社区关怀",
    )

    target_scope = db.Column(
        db.String(200),
        nullable=False,
    )

    government_text = db.Column(
        db.Text,
        nullable=False,
    )

    property_summary = db.Column(
        db.Text,
        nullable=False,
    )

    resident_message = db.Column(
        db.Text,
        nullable=False,
    )

    created_by = db.Column(
        db.String(100),
        nullable=False,
        default="government_demo",
    )

    model_mode = db.Column(
        db.String(20),
        nullable=False,
        default="mock",
    )

    # property_pending:
    # 等待物业确认任务
    #
    # resident_pending:
    # 已确认居民自愿加入，等待居民回应
    #
    # resident_ok:
    # 居民选择“我很好”
    #
    # help_requested:
    # 居民主动表示需要帮助，等待人工跟进
    #
    # remind_later:
    # 居民选择稍后提醒
    status = db.Column(
        db.String(40),
        nullable=False,
        default="property_pending",
    )

    consent_verified = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    resident_id = db.Column(
        db.String(100),
        nullable=True,
    )

    property_confirmed_by = db.Column(
        db.String(100),
        nullable=True,
    )

    resident_response = db.Column(
        db.String(40),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "service_type": self.service_type,
            "target_scope": self.target_scope,
            "government_text": self.government_text,
            "property_summary": self.property_summary,
            "resident_message": self.resident_message,
            "created_by": self.created_by,
            "model_mode": self.model_mode,
            "status": self.status,
            "consent_verified": self.consent_verified,
            "resident_id": self.resident_id,
            "property_confirmed_by": self.property_confirmed_by,
            "resident_response": self.resident_response,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
def build_care_copy(
    government_text: str,
    service_type: str,
):
    """
    AI 只负责把正式行政文本改写为：
    1. 物业可执行摘要
    2. 居民可接受的温和文案

    AI 不得判断居民风险、选择居民或决定上门。
    """

    fallback_result = {
        "property_summary": (
            f"{service_type}：请核对已自愿加入该服务的居民，"
            "由工作人员人工确认后发送一次轻量关怀提醒。"
            "不得依据摄像头、未回复状态或个人画像判断风险。"
        ),
        "resident_message": (
            "今天还好吗？点一下就好。"
            "不急，有空的时候看看；"
            "你也可以随时关闭这项关怀服务。"
        ),
        "model_mode": "mock",
    }

    ai_mode = os.getenv("AI_MODE", "mock").lower()

    if ai_mode != "live":
        return fallback_result

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return fallback_result

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=os.getenv(
                "AI_BASE_URL",
                "https://api.openai.com/v1",
            ),
        )

        prompt = f"""
你是 CommunitySense 的社区文案改写助手。

正式任务类型：
{service_type}

政府正式任务：
{government_text}

请仅输出 JSON：
{{
  "property_summary": "...",
  "resident_message": "..."
}}

要求：

1. property_summary 面向物业，80个汉字以内，清晰、可执行。
2. resident_message 面向居民，60个汉字以内，温暖、平权、不催促。
3. 居民端使用“你”，不用“您”“用户”“系统”。
4. 不得判断任何居民有风险。
5. 不得根据摄像头、未回复、独居情况选择居民。
6. 不得承诺自动上门、自动报警或自动处理。
7. 必须说明居民拥有选择权。
8. 不要增加政府原文中不存在的政策、期限或要求。
9. 不要输出风险评分。
10. 除 JSON 外不要输出任何内容。
"""

        response = client.responses.create(
            model=os.getenv(
                "AI_MODEL",
                "gpt-5.5",
            ),
            input=prompt,
        )

        output_text = response.output_text.strip()

        json_start = output_text.find("{")
        json_end = output_text.rfind("}")

        if json_start == -1 or json_end == -1:
            return fallback_result

        parsed = json.loads(
            output_text[json_start:json_end + 1]
        )

        property_summary = str(
            parsed.get("property_summary", "")
        ).strip()

        resident_message = str(
            parsed.get("resident_message", "")
        ).strip()

        if not property_summary or not resident_message:
            return fallback_result

        return {
            "property_summary": property_summary,
            "resident_message": resident_message,
            "model_mode": "live",
        }

    except Exception as error:
        print(
            f"Care task LLM fallback: {error}",
            flush=True,
        )
        return fallback_result

FORBIDDEN_FIELDS = {
    "image",
    "image_base64",
    "video",
    "video_url",
    "face",
    "face_id",
    "person_id",
    "track_id",
    "location_trace",
}

ALLOWED_EVENT_TRANSITIONS = {
    "pending": {
        "processing",
        "resolved",
        "escalated",
    },
    "processing": {
        "resolved",
        "escalated",
    },
    "escalated": {
        "processing",
        "resolved",
    },
    "resolved": {
        "reopened",
    },
    "reopened": {
        "processing",
        "resolved",
    },
}


VALID_ACTOR_ROLES = {
    "resident",
    "property",
    "committee",
    "government",
    "system",
}

TRIAGE_CATEGORIES = {
    "community_trace",
    "facility_repair",
    "community_complaint",
    "care_request",
    "urgent_help",
}

TRIAGE_ROUTES = {
    "trace_wall",
    "work_order",
    "care_service",
    "emergency_guidance",
}

TRIAGE_URGENCY_LEVELS = {
    "low",
    "medium",
    "high",
}

def compact_text(text: str, max_length: int = 42) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()

    if len(cleaned) <= max_length:
        return cleaned

    return cleaned[:max_length] + "…"


def redact_sensitive_text(text: str) -> str:
    redacted = re.sub(
        r"1[3-9]\d{9}",
        "[手机号]",
        text,
    )

    redacted = re.sub(
        r"\b\d{17}[\dXx]\b",
        "[身份证号]",
        redacted,
    )

    return redacted


def rule_based_trace_triage(text: str) -> Dict[str, Any]:
    normalized = re.sub(r"\s+", "", text).lower()

    emergency_keywords = {
        "救命",
        "着火",
        "火灾",
        "燃气泄漏",
        "晕倒",
        "昏倒",
        "失去意识",
        "呼吸困难",
        "严重出血",
        "有人受伤",
        "摔倒不起",
        "120",
        "110",
        "119",
    }

    repair_keywords = {
        "坏了",
        "不亮",
        "漏水",
        "停水",
        "停电",
        "堵塞",
        "电梯",
        "门禁",
        "路灯",
        "楼道灯",
        "照明",
        "消防通道",
        "垃圾桶",
    }

    complaint_keywords = {
        "投诉",
        "扰民",
        "噪音",
        "占道",
        "乱停车",
        "违停",
        "高空抛物",
        "堆放杂物",
    }

    care_keywords = {
        "需要帮助",
        "行动不便",
        "需要送药",
        "需要陪同",
        "高温关怀",
        "独居关怀",
        "需要社区协助",
    }

    if any(
        keyword in normalized
        for keyword in emergency_keywords
    ):
        return {
            "category": "urgent_help",
            "route": "emergency_guidance",
            "urgency": "high",
            "summary": compact_text(text),
            "allow_on_trace_wall": False,
            "reason": (
                "内容可能涉及紧急安全事件，"
                "应引导联系专业机构并进入人工协同。"
            ),
        }

    if any(
        keyword in normalized
        for keyword in repair_keywords
    ):
        return {
            "category": "facility_repair",
            "route": "work_order",
            "urgency": "medium",
            "summary": compact_text(text),
            "allow_on_trace_wall": False,
            "reason": (
                "内容属于明确的公共设施问题，"
                "应进入正式工单处理流程。"
            ),
        }

    if any(
        keyword in normalized
        for keyword in complaint_keywords
    ):
        return {
            "category": "community_complaint",
            "route": "work_order",
            "urgency": "medium",
            "summary": compact_text(text),
            "allow_on_trace_wall": False,
            "reason": (
                "内容属于投诉或治理事项，"
                "需要正式记录和责任主体处理。"
            ),
        }

    if any(
        keyword in normalized
        for keyword in care_keywords
    ):
        return {
            "category": "care_request",
            "route": "care_service",
            "urgency": "medium",
            "summary": compact_text(text),
            "allow_on_trace_wall": False,
            "reason": (
                "内容包含明确的协助请求，"
                "应进入自愿关怀服务流程。"
            ),
        }

    return {
        "category": "community_trace",
        "route": "trace_wall",
        "urgency": "low",
        "summary": compact_text(text),
        "allow_on_trace_wall": True,
        "reason": (
            "内容属于一般社区生活表达，"
            "可以发布到匿名痕迹墙。"
        ),
    }

def parse_json_object(raw_content: str) -> Dict[str, Any]:
    content = raw_content.strip()

    if content.startswith("```"):
        content = re.sub(
            r"^```(?:json)?",
            "",
            content,
        )
        content = re.sub(
            r"```$",
            "",
            content,
        )
        content = content.strip()

    start_index = content.find("{")
    end_index = content.rfind("}")

    if start_index == -1 or end_index == -1:
        raise ValueError(
            "Model response does not contain JSON"
        )

    return json.loads(
        content[start_index:end_index + 1]
    )


def validate_triage_result(
    result: Dict[str, Any],
) -> Dict[str, Any]:
    category = result.get("category")
    route = result.get("route")
    urgency = result.get("urgency")
    summary = result.get("summary")
    allow_on_trace_wall = result.get(
        "allow_on_trace_wall"
    )
    reason = result.get("reason")

    if category not in TRIAGE_CATEGORIES:
        raise ValueError("Invalid triage category")

    if route not in TRIAGE_ROUTES:
        raise ValueError("Invalid triage route")

    if urgency not in TRIAGE_URGENCY_LEVELS:
        raise ValueError("Invalid urgency level")

    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("Invalid summary")

    if not isinstance(allow_on_trace_wall, bool):
        raise ValueError(
            "allow_on_trace_wall must be boolean"
        )

    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Invalid reason")

    return {
        "category": category,
        "route": route,
        "urgency": urgency,
        "summary": compact_text(
            summary.strip(),
            max_length=60,
        ),
        "allow_on_trace_wall": allow_on_trace_wall,
        "reason": reason.strip(),
    }

def live_trace_triage(text: str) -> Dict[str, Any]:
    api_key = os.getenv(
        "OPENAI_API_KEY",
        "",
    ).strip()

    base_url = os.getenv(
        "OPENAI_BASE_URL",
        "",
    ).strip()

    model = os.getenv(
        "OPENAI_MODEL",
        "gpt-5",
    ).strip()

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing"
        )

    if not base_url:
        raise RuntimeError(
            "OPENAI_BASE_URL is missing"
        )

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,
    )

    system_prompt = """
你是 CommunitySense 社区内容分流助手。

你的任务是把居民输入分到正确通道，而不是判断某个人是否危险。

允许的 category：
community_trace
facility_repair
community_complaint
care_request
urgent_help

允许的 route：
trace_wall
work_order
care_service
emergency_guidance

允许的 urgency：
low
medium
high

规则：
1. 社区生活分享进入 trace_wall。
2. 报修和投诉进入 work_order。
3. 明确请求社区协助进入 care_service。
4. 可能涉及火灾、受伤、生命安全的内容进入 emergency_guidance。
5. 不根据文字推断独居、失联、违法或个人风险。
6. 只返回一个 JSON 对象，不要返回 Markdown。

返回字段：
category
route
urgency
summary
allow_on_trace_wall
reason
""".strip()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
    )

    raw_content = (
        response.choices[0].message.content
        or ""
    )

    parsed_result = parse_json_object(
        raw_content
    )

    return validate_triage_result(
        parsed_result
    )

def contains_forbidden_field(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child_value in value.items():
            if key.lower() in FORBIDDEN_FIELDS:
                return True

            if contains_forbidden_field(child_value):
                return True

    if isinstance(value, list):
        return any(contains_forbidden_field(item) for item in value)

    return False


@app.get("/api/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "communitysense-backend",
        }
    )


@app.post("/api/v1/sensor-readings")
def create_sensor_reading():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be JSON"}), 400

    if contains_forbidden_field(payload):
        return jsonify(
            {
                "error": (
                    "Raw media, face identifiers and personal tracking "
                    "data are not accepted."
                )
            }
        ), 400

    required_fields = {
        "protocol_version",
        "device_id",
        "area_id",
        "captured_at",
        "metrics",
    }

    missing_fields = required_fields - payload.keys()

    if missing_fields:
        return jsonify(
            {
                "error": "Missing required fields",
                "fields": sorted(missing_fields),
            }
        ), 400

    metrics = payload["metrics"]
    status = payload.get("status", {})

    if not isinstance(metrics, dict):
        return jsonify({"error": "metrics must be an object"}), 400

    if not isinstance(status, dict):
        return jsonify({"error": "status must be an object"}), 400

    try:
        motion_score = float(metrics["motion_score"])

        brightness = (
            float(metrics["brightness"])
            if metrics.get("brightness") is not None
            else None
        )

        fps = (
            float(metrics["fps"])
            if metrics.get("fps") is not None
            else None
        )
    except (KeyError, TypeError, ValueError) as exc:
        return jsonify(
            {
                "error": "Invalid sensor payload",
                "detail": str(exc),
            }
        ), 400

    if not 0 <= motion_score <= 10:
        return jsonify(
            {"error": "motion_score must be between 0 and 10"}
        ), 400

    if brightness is not None and not 0 <= brightness <= 100:
        return jsonify(
            {"error": "brightness must be between 0 and 100"}
        ), 400

    reading = SensorReading(
        protocol_version=str(payload["protocol_version"]),
        device_id=str(payload["device_id"]),
        area_id=str(payload["area_id"]),
        captured_at=str(payload["captured_at"]),
        motion_score=motion_score,
        brightness=brightness,
        fps=fps,
        rssi=status.get("rssi"),
        uptime_s=status.get("uptime_s"),
    )

    db.session.add(reading)
    db.session.commit()

    return jsonify(
        {
            "message": "Sensor reading accepted",
            "data": reading.to_dict(),
        }
    ), 201


@app.get("/api/v1/sensor-readings/latest")
def get_latest_sensor_readings():
    area_id = request.args.get("area_id")
    limit = request.args.get("limit", default=20, type=int)
    limit = max(1, min(limit, 100))

    query = SensorReading.query

    if area_id:
        query = query.filter_by(area_id=area_id)

    readings = (
        query.order_by(SensorReading.id.desc())
        .limit(limit)
        .all()
    )

    return jsonify(
        {
            "count": len(readings),
            "data": [reading.to_dict() for reading in readings],
        }
    )

@app.get("/api/v1/areas/<area_id>/summary")
def get_area_summary(area_id: str):
    limit = request.args.get("limit", default=20, type=int)
    limit = max(1, min(limit, 200))

    readings = (
        SensorReading.query
        .filter_by(area_id=area_id)
        .order_by(SensorReading.id.desc())
        .limit(limit)
        .all()
    )

    if not readings:
        return jsonify(
            {
                "error": "No sensor readings found",
                "area_id": area_id,
            }
        ), 404

    average_motion = sum(
        reading.motion_score for reading in readings
    ) / len(readings)

    brightness_values = [
        reading.brightness
        for reading in readings
        if reading.brightness is not None
    ]

    average_brightness = (
        sum(brightness_values) / len(brightness_values)
        if brightness_values
        else None
    )

    if average_motion < 2.5:
        activity_level = "low"
    elif average_motion < 6:
        activity_level = "medium"
    else:
        activity_level = "high"

    return jsonify(
        {
            "area_id": area_id,
            "sample_count": len(readings),
            "average_motion_score": round(average_motion, 2),
            "average_brightness": (
                round(average_brightness, 2)
                if average_brightness is not None
                else None
            ),
            "activity_level": activity_level,
            "latest_captured_at": readings[0].captured_at,
            "privacy": {
                "raw_media_stored": False,
                "personal_identification": False,
                "aggregation_level": "public_area",
            },
        }
    )

def build_area_snapshot(
    area_id: str,
    readings: list[SensorReading],
) -> dict[str, Any]:
    average_motion = sum(
        reading.motion_score for reading in readings
    ) / len(readings)

    brightness_values = [
        reading.brightness
        for reading in readings
        if reading.brightness is not None
    ]

    average_brightness = (
        sum(brightness_values) / len(brightness_values)
        if brightness_values
        else None
    )

    if average_motion < 2.5:
        activity_level = "low"
    elif average_motion < 6:
        activity_level = "medium"
    else:
        activity_level = "high"

    flags = []

    if (
        average_brightness is not None
        and average_brightness < 20
    ):
        flags.append(
            {
                "code": "LOW_BRIGHTNESS",
                "type": "facility",
                "message": "区域照明水平偏低，建议现场检查。",
            }
        )

    if average_motion >= 8:
        flags.append(
            {
                "code": "HIGH_ACTIVITY",
                "type": "observation",
                "message": "区域持续处于较高活跃状态。",
            }
        )

    if any(flag["code"] == "LOW_BRIGHTNESS" for flag in flags):
        attention_level = "needs_check"
    elif flags:
        attention_level = "observe"
    else:
        attention_level = "normal"

    return {
        "area_id": area_id,
        "sample_count": len(readings),
        "average_motion_score": round(average_motion, 2),
        "average_brightness": (
            round(average_brightness, 2)
            if average_brightness is not None
            else None
        ),
        "activity_level": activity_level,
        "attention_level": attention_level,
        "flags": flags,
        "latest_captured_at": readings[0].captured_at,
        "privacy": {
            "raw_media_stored": False,
            "personal_identification": False,
            "aggregation_level": "public_area",
        },
    }


@app.get("/api/v1/areas/overview")
def get_areas_overview():
    limit = request.args.get("limit", default=20, type=int)
    limit = max(1, min(limit, 200))

    area_rows = (
        db.session.query(SensorReading.area_id)
        .distinct()
        .all()
    )

    snapshots = []

    for area_row in area_rows:
        area_id = area_row[0]

        readings = (
            SensorReading.query
            .filter_by(area_id=area_id)
            .order_by(SensorReading.id.desc())
            .limit(limit)
            .all()
        )

        if readings:
            snapshots.append(
                build_area_snapshot(area_id, readings)
            )

    priority = {
        "needs_check": 2,
        "observe": 1,
        "normal": 0,
    }

    snapshots.sort(
        key=lambda item: priority[item["attention_level"]],
        reverse=True,
    )

    return jsonify(
        {
            "count": len(snapshots),
            "data": snapshots,
        }
    )

@app.post("/api/v1/areas/<area_id>/evaluate")
def evaluate_area(area_id: str):
    readings = (
        SensorReading.query
        .filter_by(area_id=area_id)
        .order_by(SensorReading.id.desc())
        .limit(20)
        .all()
    )

    if not readings:
        return jsonify(
            {
                "error": "No sensor readings found",
                "area_id": area_id,
            }
        ), 404

    snapshot = build_area_snapshot(area_id, readings)
    created_events = []

    for flag in snapshot["flags"]:
        existing_event = AreaEvent.query.filter(
            AreaEvent.area_id == area_id,
            AreaEvent.event_type == flag["code"],
            AreaEvent.status.in_(
                [
                    "pending",
                    "processing",
                    "escalated",
                    "reopened",
                ]
            ),
        ).first()

        if existing_event:
            continue

        title_map = {
            "LOW_BRIGHTNESS": "公共区域照明异常",
            "HIGH_ACTIVITY": "区域活跃度较高",
        }

        severity_map = {
            "LOW_BRIGHTNESS": "medium",
            "HIGH_ACTIVITY": "low",
        }

        event = AreaEvent(
            area_id=area_id,
            event_type=flag["code"],
            severity=severity_map.get(flag["code"], "low"),
            title=title_map.get(flag["code"], "区域状态提醒"),
            message=flag["message"],
        )

        db.session.add(event)
        created_events.append(event)

    db.session.commit()

    return jsonify(
        {
            "area": snapshot,
            "created_count": len(created_events),
            "events": [
                event.to_dict()
                for event in created_events
            ],
        }
    )

@app.get("/api/v1/events")
def get_events():
    status = request.args.get("status")
    area_id = request.args.get("area_id")

    query = AreaEvent.query

    if status:
        query = query.filter_by(status=status)

    if area_id:
        query = query.filter_by(area_id=area_id)

    events = (
        query.order_by(AreaEvent.id.desc())
        .limit(100)
        .all()
    )

    return jsonify(
        {
            "count": len(events),
            "data": [event.to_dict() for event in events],
        }
    )

@app.patch("/api/v1/events/<int:event_id>/status")
def update_event_status(event_id: int):
    event = db.session.get(AreaEvent, event_id)

    if event is None:
        return jsonify(
            {
                "error": "Event not found",
                "event_id": event_id,
            }
        ), 404

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(
            {"error": "Request body must be JSON"}
        ), 400

    new_status = payload.get("status")
    actor_role = payload.get("actor_role")
    actor_name = payload.get("actor_name")
    note = payload.get("note")

    if not isinstance(new_status, str):
        return jsonify(
            {"error": "status is required"}
        ), 400

    if actor_role not in VALID_ACTOR_ROLES:
        return jsonify(
            {
                "error": "Invalid actor_role",
                "allowed_roles": sorted(VALID_ACTOR_ROLES),
            }
        ), 400

    if not isinstance(actor_name, str) or not actor_name.strip():
        return jsonify(
            {"error": "actor_name is required"}
        ), 400

    if note is not None and not isinstance(note, str):
        return jsonify(
            {"error": "note must be a string"}
        ), 400

    allowed_statuses = ALLOWED_EVENT_TRANSITIONS.get(
        event.status,
        set(),
    )

    if new_status not in allowed_statuses:
        return jsonify(
            {
                "error": "Invalid status transition",
                "current_status": event.status,
                "requested_status": new_status,
                "allowed_statuses": sorted(allowed_statuses),
            }
        ), 400

    previous_status = event.status
    event.status = new_status

    transition = EventTransition(
        event_id=event.id,
        from_status=previous_status,
        to_status=new_status,
        actor_role=actor_role,
        actor_name=actor_name.strip(),
        note=note.strip() if note else None,
    )

    db.session.add(transition)
    db.session.commit()

    return jsonify(
        {
            "message": "Event status updated",
            "event": event.to_dict(),
            "transition": transition.to_dict(),
        }
    )

@app.get("/api/v1/events/<int:event_id>")
def get_event_detail(event_id: int):
    event = db.session.get(AreaEvent, event_id)

    if event is None:
        return jsonify(
            {
                "error": "Event not found",
                "event_id": event_id,
            }
        ), 404

    transitions = (
        EventTransition.query
        .filter_by(event_id=event_id)
        .order_by(EventTransition.id.asc())
        .all()
    )

    return jsonify(
        {
            "event": event.to_dict(),
            "history": [
                transition.to_dict()
                for transition in transitions
            ],
        }
    )

@app.post("/api/v1/ai/trace-triage")
def trace_triage():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(
            {"error": "Request body must be JSON"}
        ), 400

    area_id = payload.get("area_id")
    text = payload.get("text")

    if not isinstance(area_id, str) or not area_id.strip():
        return jsonify(
            {"error": "area_id is required"}
        ), 400

    if not isinstance(text, str):
        return jsonify(
            {"error": "text is required"}
        ), 400

    text = text.strip()

    if len(text) < 2:
        return jsonify(
            {
                "error": (
                    "text must contain at least "
                    "2 characters"
                )
            }
        ), 400

    if len(text) > 500:
        return jsonify(
            {
                "error": (
                    "text must not exceed "
                    "500 characters"
                )
            }
        ), 400

    sanitized_text = redact_sensitive_text(
        text
    )

    ai_mode = os.getenv(
        "AI_MODE",
        "mock",
    ).strip().lower()

    fallback_used = False
    fallback_reason = None

    if ai_mode == "live":
        try:
            result = live_trace_triage(
                sanitized_text
            )
            source = "live_ai"

        except Exception as exc:
            result = rule_based_trace_triage(
                sanitized_text
            )
            source = "rule_fallback"
            fallback_used = True
            fallback_reason = (
                exc.__class__.__name__
            )

    else:
        result = rule_based_trace_triage(
            sanitized_text
        )
        source = "mock_rules"

    return jsonify(
        {
            "area_id": area_id.strip(),
            "result": result,
            "source": source,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "privacy": {
                "raw_text_persisted": False,
                "personal_risk_inference": False,
                "sensitive_fields_redacted": True,
            },
        }
    )

# ============================================================
# Care task APIs
# Government -> Property -> Resident
# ============================================================


@app.post("/api/v1/care-tasks")
def create_care_task():
    data = request.get_json(silent=True) or {}

    government_text = str(
        data.get("government_text", "")
    ).strip()

    service_type = str(
        data.get("service_type", "社区关怀")
    ).strip()

    target_scope = str(
        data.get("target_scope", "")
    ).strip()

    if not government_text:
        return jsonify({
            "error": "government_text is required",
        }), 400

    if not target_scope:
        return jsonify({
            "error": "target_scope is required",
        }), 400

    # 政府创建阶段不允许直接指定某个居民。
    if data.get("resident_id"):
        return jsonify({
            "error": (
                "Government task creation cannot "
                "select an individual resident."
            ),
        }), 400

    generated = build_care_copy(
        government_text=government_text,
        service_type=service_type,
    )

    task = CareTask(
        id=f"CARE-{uuid.uuid4().hex[:12].upper()}",
        service_type=service_type,
        target_scope=target_scope,
        government_text=government_text,
        property_summary=generated[
            "property_summary"
        ],
        resident_message=generated[
            "resident_message"
        ],
        created_by=str(
            data.get(
                "created_by",
                "government_demo",
            )
        ),
        model_mode=generated["model_mode"],
        status="property_pending",
    )

    db.session.add(task)
    db.session.commit()

    return jsonify({
        "message": "Care task created.",
        "task": task.to_dict(),
        "ai_boundary": {
            "selects_resident": False,
            "infers_risk": False,
            "automatic_visit": False,
        },
    }), 201

@app.get("/api/v1/property/care-tasks")
def get_property_care_tasks():
    status = request.args.get("status")

    query = CareTask.query

    if status:
        query = query.filter_by(status=status)

    tasks = query.order_by(
        CareTask.created_at.desc()
    ).all()

    return jsonify({
        "count": len(tasks),
        "tasks": [
            {
                "id": task.id,
                "service_type": task.service_type,
                "target_scope": task.target_scope,
                "property_summary": (
                    task.property_summary
                ),
                "status": task.status,
                "created_at": (
                    task.created_at.isoformat()
                ),
                "source": {
                    "type": "government_task",
                    "created_by": task.created_by,
                },
            }
            for task in tasks
        ],
    })

@app.post(
    "/api/v1/care-tasks/<task_id>/property-confirm"
)
def confirm_care_task(task_id):
    task = CareTask.query.get_or_404(task_id)

    data = request.get_json(silent=True) or {}

    consent_verified = (
        data.get("consent_verified") is True
    )

    resident_id = str(
        data.get("resident_id", "")
    ).strip()

    confirmed_by = str(
        data.get("confirmed_by", "")
    ).strip()

    if not consent_verified:
        return jsonify({
            "error": (
                "The property worker must manually "
                "confirm that the resident opted in."
            ),
        }), 400

    if not resident_id:
        return jsonify({
            "error": "resident_id is required",
        }), 400

    if not confirmed_by:
        return jsonify({
            "error": "confirmed_by is required",
        }), 400

    task.consent_verified = True
    task.resident_id = resident_id
    task.property_confirmed_by = confirmed_by
    task.status = "resident_pending"
    task.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "message": (
            "Resident care card is ready."
        ),
        "task": task.to_dict(),
        "note": (
            "The resident was selected through "
            "manual opt-in verification, not AI "
            "or sensor inference."
        ),
    })

@app.get("/api/v1/resident/care-cards")
def get_resident_care_cards():
    resident_id = str(
        request.args.get("resident_id", "")
    ).strip()

    if not resident_id:
        return jsonify({
            "error": "resident_id is required",
        }), 400

    tasks = (
        CareTask.query
        .filter_by(
            resident_id=resident_id,
            consent_verified=True,
        )
        .filter(
            CareTask.status.in_([
                "resident_pending",
                "remind_later",
            ])
        )
        .order_by(
            CareTask.created_at.desc()
        )
        .all()
    )

    return jsonify({
        "count": len(tasks),
        "cards": [
            {
                "task_id": task.id,
                "type": "care_card",
                "service_type": task.service_type,
                "message": task.resident_message,
                "choices": [
                    {
                        "value": "ok",
                        "text": "我很好",
                    },
                    {
                        "value": "need_help",
                        "text": "需要帮助",
                    },
                    {
                        "value": "remind_later",
                        "text": "稍后提醒",
                    },
                ],
                "privacy_note": (
                    "这张卡片来自你自愿加入的社区服务，"
                    "不是根据摄像头或个人画像生成的。"
                ),
            }
            for task in tasks
        ],
    })

@app.post(
    "/api/v1/care-tasks/<task_id>/resident-response"
)
def submit_resident_response(task_id):
    task = CareTask.query.get_or_404(task_id)

    data = request.get_json(silent=True) or {}

    resident_id = str(
        data.get("resident_id", "")
    ).strip()

    response_value = str(
        data.get("response", "")
    ).strip()

    allowed_responses = {
        "ok",
        "need_help",
        "remind_later",
    }

    if resident_id != task.resident_id:
        return jsonify({
            "error": "Resident does not match task.",
        }), 403

    if response_value not in allowed_responses:
        return jsonify({
            "error": (
                "response must be ok, need_help, "
                "or remind_later"
            ),
        }), 400

    task.resident_response = response_value
    task.updated_at = datetime.utcnow()

    if response_value == "ok":
        task.status = "resident_ok"
        reply = "收到，今天也照顾好自己。"

    elif response_value == "need_help":
        task.status = "help_requested"
        reply = (
            "收到。社区值守台会人工查看你的请求。"
            "系统不会自动判断风险，也不会自动上门。"
        )

    else:
        task.status = "remind_later"
        reply = "好，不急，晚一点再提醒你。"

    db.session.commit()

    return jsonify({
        "message": reply,
        "task_id": task.id,
        "status": task.status,
        "requires_human_review": (
            response_value == "need_help"
        ),
        "automatic_visit": False,
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )