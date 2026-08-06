from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import base64
import csv
import json
import time
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 测试时优先缩短等待时间；需要高质量结果时可在 .env 中覆盖。
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")
IMAGE_SIZE = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")
IMAGE_QUALITY = os.getenv("OPENAI_IMAGE_QUALITY", "low")
IMAGE_FORMAT = os.getenv("OPENAI_IMAGE_FORMAT", "jpeg")
IMAGE_COMPRESSION = int(os.getenv("OPENAI_IMAGE_COMPRESSION", "85"))

# 每位测试者使用独立状态，避免多人测试时互相污染对话和图片。
sessions = {}

# 保存生成图片的文件夹
IMAGE_DIR = "generated_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# 保存问卷的文件夹
SURVEY_DIR = "survey_results"
os.makedirs(SURVEY_DIR, exist_ok=True)


def save_base64_image(image_base64, prefix="character", extension="jpeg"):
    """把 API 返回的 base64 图片保存到本地文件，返回文件路径"""
    image_bytes = base64.b64decode(image_base64)
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.{extension}"
    file_path = os.path.join(IMAGE_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    return file_path


def get_session(data):
    """取得当前测试者的独立会话。"""
    session_id = str(data.get("session_id", "default"))[:128]
    if not session_id:
        session_id = "default"

    state = sessions.setdefault(
        session_id,
        {"conversation_memory": [], "latest_image_path": None}
    )
    return session_id, state


def image_request_options():
    options = {
        "model": IMAGE_MODEL,
        "size": IMAGE_SIZE,
        "quality": IMAGE_QUALITY,
        "output_format": IMAGE_FORMAT,
    }

    if IMAGE_FORMAT in {"jpeg", "webp"}:
        options["output_compression"] = IMAGE_COMPRESSION

    return options


def append_csv_row(file_path, headers, row):
    """如果 CSV 不存在则写入表头，然后追加一行"""
    file_exists = os.path.exists(file_path)

    with open(file_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


@app.route("/api/generate", methods=["POST"])
def generate_character():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "message is required"}), 400

    _, state = get_session(data)
    state["conversation_memory"].append(message)
    recent_context = "\n".join(state["conversation_memory"][-6:])
    started_at = time.perf_counter()

    try:
        # 第一次：根据用户输入直接生成
        if state["latest_image_path"] is None:
            prompt = f"""
User requests:
{recent_context}

Create one centered, full-body virtual character with a clean composition.
"""

            result = client.images.generate(
                prompt=prompt,
                **image_request_options()
            )

            image_base64 = result.data[0].b64_json
            state["latest_image_path"] = save_base64_image(
                image_base64,
                prefix="character",
                extension=IMAGE_FORMAT
            )

            reply = "生成しました。"

        # 第二次以后：基于上一张图，根据用户输入修改
        else:
            edit_prompt = f"""
Conversation history:
{recent_context}

Latest user request:
{message}
"""

            with open(state["latest_image_path"], "rb") as image_file:
                result = client.images.edit(
                    image=image_file,
                    prompt=edit_prompt,
                    **image_request_options()
                )

            image_base64 = result.data[0].b64_json
            state["latest_image_path"] = save_base64_image(
                image_base64,
                prefix="character_edit",
                extension=IMAGE_FORMAT
            )

            reply = "修正しました。"

        elapsed_seconds = round(time.perf_counter() - started_at, 1)
        image_url = f"data:image/{IMAGE_FORMAT};base64,{image_base64}"

        return jsonify({
            "reply": reply,
            "image": image_url,
            "elapsed_seconds": elapsed_seconds,
            "generation": {
                "model": IMAGE_MODEL,
                "size": IMAGE_SIZE,
                "quality": IMAGE_QUALITY
            }
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/save-survey", methods=["POST"])
def save_survey():
    data = request.get_json(silent=True) or {}

    survey_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp = datetime.now().isoformat()

    summary_file = os.path.join(SURVEY_DIR, "survey_summary.csv")
    image_rating_file = os.path.join(SURVEY_DIR, "image_ratings.csv")

    # 1) 保存总体问卷
    summary_headers = [
        "survey_id",
        "timestamp",
        "session_id",
        "generation_count",
        "generation_times",
        "average_generation_seconds",
        "experience",
        "dialogue",
        "match",
        "consistency",
        "control",
        "retry",
        "problem",
        "suggestion",
        "scene",
        "user_prompts"
    ]

    summary_row = {
        "survey_id": survey_id,
        "timestamp": timestamp,
        "session_id": data.get("session_id", ""),
        "generation_count": data.get("generation_count", ""),
        "generation_times": json.dumps(
            data.get("generation_times", []), ensure_ascii=False
        ),
        "average_generation_seconds": data.get(
            "average_generation_seconds", ""
        ),
        "experience": data.get("experience", ""),
        "dialogue": data.get("dialogue", ""),
        "match": data.get("match", ""),
        "consistency": data.get("consistency", ""),
        "control": data.get("control", ""),
        "retry": data.get("retry", ""),
        "problem": data.get("problem", ""),
        "suggestion": data.get("suggestion", ""),
        "scene": data.get("scene", ""),
        "user_prompts": data.get("user_prompts", "")
    }

    append_csv_row(summary_file, summary_headers, summary_row)

    # 2) 保存每张生成图的评分
    image_rating_headers = [
        "survey_id",
        "timestamp",
        "version",
        "prompt",
        "rating",
        "generation_seconds"
    ]

    image_ratings = data.get("image_ratings", [])

    for item in image_ratings:
        row = {
            "survey_id": survey_id,
            "timestamp": timestamp,
            "version": item.get("version", ""),
            "prompt": item.get("prompt", ""),
            "rating": item.get("rating", ""),
            "generation_seconds": item.get("generation_seconds", "")
        }

        append_csv_row(image_rating_file, image_rating_headers, row)

    print(f"SURVEY SAVED: {survey_id}")

    return jsonify({
        "message": "survey and image ratings saved",
        "survey_id": survey_id
    })


@app.route("/api/reset", methods=["POST"])
def reset_character():
    data = request.get_json(silent=True) or {}
    session_id = str(data.get("session_id", "default"))[:128] or "default"
    sessions.pop(session_id, None)

    print(f"RESET OK: session {session_id} cleared")

    return jsonify({"message": "reset ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
