from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import base64
import csv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 单用户测试状态
conversation_memory = []
latest_image_path = None

# 保存生成图片的文件夹
IMAGE_DIR = "generated_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# 保存问卷的文件夹
SURVEY_DIR = "survey_results"
os.makedirs(SURVEY_DIR, exist_ok=True)


def save_base64_image(image_base64, prefix="character"):
    """把 API 返回的 base64 图片保存到本地文件，返回文件路径"""
    image_bytes = base64.b64decode(image_base64)
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    file_path = os.path.join(IMAGE_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    return file_path


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
    global latest_image_path, conversation_memory

    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "message is required"}), 400

    conversation_memory.append(message)
    recent_context = "\n".join(conversation_memory[-6:])

    try:
        # 第一次：根据用户输入直接生成
        if latest_image_path is None:
            prompt = f"""
User requests:
{recent_context}
"""

            result = client.images.generate(
                model="gpt-image-2",
                prompt=prompt,
                size="1024x1536",
                quality="medium"
            )

            image_base64 = result.data[0].b64_json
            latest_image_path = save_base64_image(
                image_base64,
                prefix="character"
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

            with open(latest_image_path, "rb") as image_file:
                result = client.images.edit(
                    model="gpt-image-2",
                    image=image_file,
                    prompt=edit_prompt,
                    size="1024x1536"
                )

            image_base64 = result.data[0].b64_json
            latest_image_path = save_base64_image(
                image_base64,
                prefix="character_edit"
            )

            reply = "修正しました。"

        image_url = f"data:image/png;base64,{image_base64}"

        return jsonify({
            "reply": reply,
            "image": image_url
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/save-survey", methods=["POST"])
def save_survey():
    data = request.get_json()

    survey_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp = datetime.now().isoformat()

    summary_file = os.path.join(SURVEY_DIR, "survey_summary.csv")
    image_rating_file = os.path.join(SURVEY_DIR, "image_ratings.csv")

    # 1) 保存总体问卷
    summary_headers = [
        "survey_id",
        "timestamp",
        "generation_count",
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
        "generation_count": data.get("generation_count", ""),
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
        "rating"
    ]

    image_ratings = data.get("image_ratings", [])

    for item in image_ratings:
        row = {
            "survey_id": survey_id,
            "timestamp": timestamp,
            "version": item.get("version", ""),
            "prompt": item.get("prompt", ""),
            "rating": item.get("rating", "")
        }

        append_csv_row(image_rating_file, image_rating_headers, row)

    print(f"SURVEY SAVED: {survey_id}")

    return jsonify({
        "message": "survey and image ratings saved",
        "survey_id": survey_id
    })


@app.route("/api/reset", methods=["POST"])
def reset_character():
    global latest_image_path, conversation_memory

    latest_image_path = None
    conversation_memory = []

    print("RESET OK: conversation_memory cleared, latest_image_path cleared")

    return jsonify({"message": "reset ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)