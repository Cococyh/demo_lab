from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import base64
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 简单的单用户测试状态
conversation_memory = []
latest_image_path = None

# 保存图片的文件夹
IMAGE_DIR = "generated_images"
os.makedirs(IMAGE_DIR, exist_ok=True)


def save_base64_image(image_base64, prefix="character"):
    """把 API 返回的 base64 图片保存到本地文件，返回文件路径"""
    image_bytes = base64.b64decode(image_base64)
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    file_path = os.path.join(IMAGE_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    return file_path


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
        # 第一次：直接生成
        if latest_image_path is None:
            prompt = f"""
                    Create an anime / manga style illustration of one original cool female character.

                    This is for a university research demo about interactive character design.

                    User requests so far:
                    {recent_context}

                    Requirements:
                    - One female character
                    - Anime / manga style
                    - Stylish and memorable design
                    - Clean composition
                    - Upper body or full body
                    - No text, no logo, no watermark
                    - Good quality character illustration
                    """

            result = client.images.generate(
                model="gpt-image-2",
                prompt=prompt,
                size="1024x1536",
                quality="medium"
            )

            image_base64 = result.data[0].b64_json
            latest_image_path = save_base64_image(image_base64, prefix="character")

            reply = "分かりました。そのイメージをもとにキャラクターを生成しました。"

        # 第二次以后：基于上一张图修改
        else:
            edit_prompt = f"""
Edit the provided character image.

This is the SAME character as before.
Preserve the same character identity as much as possible:
- keep the same person
- preserve face impression
- preserve hairstyle unless the user explicitly asks to change it
- preserve outfit style unless the user explicitly asks to change it
- preserve the overall vibe unless the user explicitly asks to change it

Conversation history:
{recent_context}

Latest user request:
{message}

Important:
- Modify only what the user asked for
- Do not turn the character into a completely different person
- Keep the character visually consistent
- Anime / manga style
- No text, no logo, no watermark
"""

            with open(latest_image_path, "rb") as image_file:
                result = client.images.edit(
                    model="gpt-image-2",
                    image=image_file,
                    prompt=edit_prompt,
                    size="1024x1536"
                )

            image_base64 = result.data[0].b64_json
            latest_image_path = save_base64_image(image_base64, prefix="character_edit")

            reply = "分かりました。前回の画像をもとに修正しました。"

        image_url = f"data:image/png;base64,{image_base64}"

        return jsonify({
            "reply": reply,
            "image": image_url
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/reset", methods=["POST"])
def reset_character():
    global latest_image_path, conversation_memory
    latest_image_path = None
    conversation_memory = []
    print("RESET OK: conversation_memory cleared, latest_image_path cleared")
    return jsonify({"message": "reset ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)