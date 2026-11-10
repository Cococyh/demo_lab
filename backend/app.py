from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random
import time
import uuid
from dotenv import load_dotenv
import os
import base64
import csv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

# ---------- ComfyUI 本地推理配置（可在 .env 中覆盖） ----------
COMFY_URL = os.getenv("COMFY_URL", "http://127.0.0.1:8188")
# 模型文件需放在 ComfyUI 的 models/checkpoints 下（例如 E:\AI\ComfyUI\models\checkpoints）
COMFY_CHECKPOINT = os.getenv("COMFY_CHECKPOINT", "your_model.safetensors")
COMFY_NEGATIVE = os.getenv(
    "COMFY_NEGATIVE",
    "lowres, bad anatomy, bad hands, extra fingers, missing fingers, "
    "worst quality, low quality, blurry, watermark, text, cropped",
)
COMFY_QUALITY_TAGS = os.getenv("COMFY_QUALITY_TAGS", "masterpiece, best quality, ")
COMFY_WIDTH = int(os.getenv("COMFY_WIDTH", "832"))
COMFY_HEIGHT = int(os.getenv("COMFY_HEIGHT", "1216"))
COMFY_STEPS = int(os.getenv("COMFY_STEPS", "28"))
COMFY_CFG = float(os.getenv("COMFY_CFG", "6.5"))
COMFY_SAMPLER = os.getenv("COMFY_SAMPLER", "euler_ancestral")
COMFY_SCHEDULER = os.getenv("COMFY_SCHEDULER", "normal")
# 修改图片时的重绘强度：越小越接近上一张图
COMFY_EDIT_DENOISE = float(os.getenv("COMFY_EDIT_DENOISE", "0.6"))
COMFY_TIMEOUT = int(os.getenv("COMFY_TIMEOUT", "300"))

# 单用户测试状态
conversation_memory = []
latest_image_path = None

# 保存生成图片的文件夹
IMAGE_DIR = "generated_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# 保存问卷的文件夹
SURVEY_DIR = "survey_results"
os.makedirs(SURVEY_DIR, exist_ok=True)


def save_image_bytes(image_bytes, prefix="character"):
    """把图片字节保存到本地文件，返回文件路径"""
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    file_path = os.path.join(IMAGE_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    return file_path


def upload_to_comfy(file_path):
    """把本地图片上传到 ComfyUI 的 input 目录，返回其文件名"""
    with open(file_path, "rb") as f:
        r = requests.post(
            f"{COMFY_URL}/upload/image",
            files={"image": (os.path.basename(file_path), f, "image/png")},
            data={"overwrite": "true"},
            timeout=60,
        )
    r.raise_for_status()
    return r.json()["name"]


def build_workflow(prompt_text, input_image=None):
    """构造 ComfyUI API 格式工作流。input_image 为 None 时文生图，否则图生图。"""
    seed = random.randint(0, 2**32 - 1)
    wf = {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": COMFY_CHECKPOINT}},
        "2": {"class_type": "CLIPTextEncode",
              "inputs": {"text": COMFY_QUALITY_TAGS + prompt_text, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode",
              "inputs": {"text": COMFY_NEGATIVE, "clip": ["1", 1]}},
        "6": {"class_type": "VAEDecode",
              "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage",
              "inputs": {"images": ["6", 0], "filename_prefix": "demo_lab"}},
    }

    if input_image is None:
        wf["4"] = {"class_type": "EmptyLatentImage",
                   "inputs": {"width": COMFY_WIDTH, "height": COMFY_HEIGHT, "batch_size": 1}}
        denoise = 1.0
    else:
        wf["8"] = {"class_type": "LoadImage", "inputs": {"image": input_image}}
        wf["9"] = {"class_type": "ImageScale",
                   "inputs": {"image": ["8", 0], "upscale_method": "lanczos",
                              "width": COMFY_WIDTH, "height": COMFY_HEIGHT, "crop": "center"}}
        wf["4"] = {"class_type": "VAEEncode",
                   "inputs": {"pixels": ["9", 0], "vae": ["1", 2]}}
        denoise = COMFY_EDIT_DENOISE

    wf["5"] = {"class_type": "KSampler",
               "inputs": {"model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0],
                          "latent_image": ["4", 0], "seed": seed, "steps": COMFY_STEPS,
                          "cfg": COMFY_CFG, "sampler_name": COMFY_SAMPLER,
                          "scheduler": COMFY_SCHEDULER, "denoise": denoise}}
    return wf


def run_comfy(prompt_text, input_path=None):
    """提交工作流到本地 ComfyUI，等待完成，返回 PNG 字节"""
    input_image = upload_to_comfy(input_path) if input_path else None
    workflow = build_workflow(prompt_text, input_image)

    r = requests.post(
        f"{COMFY_URL}/prompt",
        json={"prompt": workflow, "client_id": str(uuid.uuid4())},
        timeout=30,
    )
    if r.status_code != 200:
        raise RuntimeError(f"ComfyUI rejected workflow: {r.text}")
    prompt_id = r.json()["prompt_id"]

    deadline = time.time() + COMFY_TIMEOUT
    while time.time() < deadline:
        h = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=30).json()
        if prompt_id in h:
            entry = h[prompt_id]
            if entry.get("status", {}).get("status_str") == "error":
                raise RuntimeError(f"ComfyUI execution error: {entry['status']}")
            for node_out in entry.get("outputs", {}).values():
                for img in node_out.get("images", []):
                    v = requests.get(
                        f"{COMFY_URL}/view",
                        params={"filename": img["filename"],
                                "subfolder": img.get("subfolder", ""),
                                "type": img.get("type", "output")},
                        timeout=60,
                    )
                    v.raise_for_status()
                    return v.content
        time.sleep(1)
    raise TimeoutError("ComfyUI generation timed out")


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
        # 第一次：文生图
        if latest_image_path is None:
            image_bytes = run_comfy(recent_context)
            latest_image_path = save_image_bytes(image_bytes, prefix="character")
            reply = "生成しました。"

        # 第二次以后：基于上一张图做图生图修改
        else:
            image_bytes = run_comfy(recent_context, input_path=latest_image_path)
            latest_image_path = save_image_bytes(image_bytes, prefix="character_edit")
            reply = "修正しました。"

        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
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