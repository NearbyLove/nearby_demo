import hashlib
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AuthenticationError, OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

if not ENV_FILE.exists():
    raise RuntimeError(
        f".env file not found: {ENV_FILE}"
    )

# override=True 很重要：
# 即使当前终端里还残留着旧 Key，也强制使用 .env 中的新 Key。
load_dotenv(
    dotenv_path=ENV_FILE,
    override=True,
)

api_key = os.getenv("OPENAI_API_KEY", "").strip()
base_url = os.getenv("OPENAI_BASE_URL", "").strip()
model = os.getenv("OPENAI_MODEL", "").strip()

if not api_key:
    raise RuntimeError("OPENAI_API_KEY is missing")

if not api_key.startswith("sk-"):
    raise RuntimeError(
        "OPENAI_API_KEY does not start with sk-"
    )

if "*" in api_key:
    raise RuntimeError(
        "OPENAI_API_KEY contains *, so it is a masked key"
    )

if not base_url:
    raise RuntimeError("OPENAI_BASE_URL is missing")

if not model:
    raise RuntimeError("OPENAI_MODEL is missing")

# 只打印不可逆指纹，不打印完整密钥。
key_fingerprint = hashlib.sha256(
    api_key.encode("utf-8")
).hexdigest()[:12]

print(
    {
        "env_file": str(ENV_FILE),
        "key_starts_with_sk": api_key.startswith("sk-"),
        "key_length": len(api_key),
        "key_fingerprint": key_fingerprint,
        "base_url": base_url,
        "model": model,
    }
)

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=30.0,
)

try:
    response = client.responses.create(
        model=model,
        input="只回复：CommunitySense API connected",
        instructions="You are a helpful assistant.",
    )

    print(response.output_text)


except AuthenticationError:
    print(
        "认证失败：当前 .env 中的 Key "
        "仍被网关判定为无效。"
    )
    raise