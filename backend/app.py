from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
import re
import json
import time
import uuid
import base64
import csv
import random
import threading
import unicodedata
import requests
from datetime import datetime

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 构建后的前端（frontend/dist）由后端一起托管，现场只需要访问一个地址
FRONTEND_DIST = os.path.join(os.path.dirname(BASE_DIR), "frontend", "dist")

app = Flask(__name__, static_folder=FRONTEND_DIST, static_url_path="")
CORS(app)

# 本地 ComfyUI（E:\AI\Start-ComfyUI.cmd 启动，默认 127.0.0.1:8188）
COMFY_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
COMFY_TIMEOUT = int(os.getenv("COMFYUI_TIMEOUT", "300"))
WORKFLOW_DIR = os.path.join(BASE_DIR, "workflows")
# 本地模型：Qwen Image 2.1 官方 Turbo（qwen_image_2.1_turbo_int8_convrot），8 步，Euler，CFG 1.0，
# 官方固定噪声表，文本编码器 qwen3vl_8b_int8_convrot。
# workflows/*.json 由 tools/build_workflows.py 从 ComfyUI 自带的官方 Turbo 模板生成，不要手动修改；
# 与官方唯一的不同是文生图画布 1024x1536（竖图 2:3，约 157 万像素）。
# 修改方式（v1.2〜）：不用编辑模型。输入栏保留上一次的全文，参加者改写全文后，
# 用"基准版本的同一个种子"重新文生图 → 构图大致保留，写进文字的变化（发型、年龄感、去掉眼镜等）都能体现。
# 全文与基准版本完全相同（原样再发送）时换新种子，相当于"换一个方案"。

# 图片和日志（都不提交到仓库，见 .gitignore）
IMAGE_DIR = os.path.join(BASE_DIR, "generated_images")
LOG_DIR = os.path.join(BASE_DIR, "logs")

GENERATION_LOG = os.path.join(LOG_DIR, "generation_log.csv")
GENERATION_HEADERS = [
    "timestamp", "participant_id", "version", "action", "base_version",
    "prompt", "input_language", "duration_sec", "image_file", "error", "seed",
]
EVENT_LOG = os.path.join(LOG_DIR, "event_log.csv")
EVENT_HEADERS = ["timestamp", "participant_id", "event", "version", "detail"]
# 线上参加者在网站里填写的问卷（与纸质问卷同一内容；选项用与语言无关的代码保存）
SURVEY_LOG = os.path.join(LOG_DIR, "survey_log.csv")
SURVEY_HEADERS = [
    "timestamp", "participant_id", "mode", "final_version", "ui_language",
    # 列名は番号を付けない（紙・ウェブ共通。番号は 質問3 clearer / 4 satisfaction / 5 focus /
    # 6 difficulty / 7 reason / 8 comment。質問1・2 は開始時に event_log の pre_experience / pre_clarity）
    "clearer", "satisfaction",
    "focus", "focus_other", "difficulty", "difficulty_other", "reason", "reason_other", "comment",
]
SURVEY_CHOICES = {
    "q4": {"face", "hair", "clothes", "body", "pose", "background", "style", "mood", "other"},
    "q5": {"start_what", "start_how", "edit_next", "edit_nochange", "edit_overchange", "edit_quality",
           "wait_long", "ui_hard", "other", "none"},
    "q6": {"satisfied", "gave_up", "no_idea", "tired", "time_up", "other"},
}

# 单台设备、一次一人：当前参加者的状态（开始新参加者时清空）
state = {"participant_id": None, "version": 0, "latest_image_path": None, "last_active": 0.0}
# 有人正在参加时，别的 ID 不能开始（也不能把会话切走）。前端每 30 秒发一次 /api/ping；
# 超过这个秒数没有任何请求，就当作那个人已经离开（关掉了页面却没按"终了"）
BUSY_TIMEOUT = int(os.getenv("BUSY_TIMEOUT", "180"))


def id_already_used(participant_id):
    """这个 ID 是否已经被用过（正式日志、图片文件夹、预测试 logs/pilot 都算）。
    900〜999 是测试用 ID，总是可以重复使用（测完会删除）"""
    if not participant_id or (participant_id.isdigit() and 900 <= int(participant_id) <= 999):
        return False
    if os.path.isdir(os.path.join(IMAGE_DIR, participant_id)):
        return True
    for log in (EVENT_LOG, os.path.join(LOG_DIR, "pilot", "event_log.csv")):
        if any(r.get("participant_id") == participant_id and r.get("event") == "start" for r in read_csv(log)):
            return True
    return os.path.isdir(os.path.join(LOG_DIR, "pilot", "generated_images", participant_id))


def someone_else_active(participant_id):
    """当前有别的参加者正在进行（最近有请求）时返回 True。调用方需持有 state_lock"""
    current = state["participant_id"]
    return bool(current) and current != participant_id and time.time() - state["last_active"] < BUSY_TIMEOUT
state_lock = threading.Lock()


def load_workflow(name):
    with open(os.path.join(WORKFLOW_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def run_comfy(workflow):
    """提交 API 格式工作流到 ComfyUI，轮询直到完成，返回第一张输出图片的字节"""
    r = requests.post(f"{COMFY_URL}/prompt",
                      json={"prompt": workflow, "client_id": str(uuid.uuid4())}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"ComfyUI 拒绝了工作流: {r.text}")
    prompt_id = r.json()["prompt_id"]

    deadline = time.time() + COMFY_TIMEOUT
    while time.time() < deadline:
        hist = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=30).json()
        if prompt_id in hist:
            entry = hist[prompt_id]
            if entry.get("status", {}).get("status_str") == "error":
                raise RuntimeError(f"ComfyUI 执行失败: {entry['status']}")
            for node in entry.get("outputs", {}).values():
                for img in node.get("images", []):
                    resp = requests.get(f"{COMFY_URL}/view", params={
                        "filename": img["filename"],
                        "subfolder": img.get("subfolder", ""),
                        "type": img.get("type", "output")}, timeout=60)
                    resp.raise_for_status()
                    return resp.content
            raise RuntimeError("ComfyUI 没有返回图片")
        time.sleep(0.5)
    raise TimeoutError("ComfyUI 生成超时")


def new_seed():
    return random.randint(0, 2**31 - 1)


def comfy_text_to_image(prompt, seed):
    wf = load_workflow("text_to_image_api.json")
    wf["encode"]["inputs"]["prompt"] = prompt  # 参加者的原文，不加任何修饰
    wf["noise"]["inputs"]["noise_seed"] = seed
    return run_comfy(wf)


def version_record(participant_id, version):
    """生成日志里某一版的记录（全文和种子）；找不到返回 None"""
    rows = [r for r in read_csv(GENERATION_LOG)
            if r.get("participant_id") == participant_id and r.get("version") == str(version)]
    return rows[-1] if rows else None


def detect_language(text):
    """粗略判断输入语言：ja / zh / en / other（仅用于日志）"""
    if re.search(r"[\u3040-\u30ff]", text):
        return "ja"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"[A-Za-z]", text):
        return "en"
    return "other"


def normalize_id(value):
    """全角英数字（日文输入法容易打出「Ｐ０２」）先转成半角，并去掉前后空白"""
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def safe_id(value):
    """参加者ID只保留字母数字、下划线和连字符（用于文件名）"""
    return re.sub(r"[^0-9A-Za-z_\-]", "", normalize_id(value))[:32]


# 显示给参加者的出错提示（日语、不含技术信息；技术细节只写进日志）
# 前端按 code 显示成参加者选的语言（日/中/英），error 里的日语作为后备
MSG_NO_ID = "参加者IDを入力してください。"
MSG_BAD_ID = "参加者IDは半角の英数字で入力してください。"
MSG_NO_SESSION = "参加者IDを確認できませんでした。実験者に知らせてください。"
MSG_NO_MESSAGE = "メッセージを入力してください。"
MSG_COMFY_DOWN = "画像生成エンジンに接続できません。実験者に知らせてください。"
MSG_TIMEOUT = "時間がかかりすぎたため中断しました。もう一度送信してください。"
MSG_GEN_FAILED = "画像を作れませんでした。もう一度送信してください。続く場合は実験者に知らせてください。"
MSG_BAD_VERSION = "その画像は選べません。"
MSG_BUSY = "現在、ほかの方が参加中です。終わるまで少しお待ちください。"
MSG_ID_USED = "このIDはすでに使われています。別のIDを入力してください。"


ERROR_CODES = {MSG_NO_ID: "NO_ID", MSG_BAD_ID: "BAD_ID", MSG_NO_SESSION: "NO_SESSION",
               MSG_NO_MESSAGE: "NO_MESSAGE", MSG_COMFY_DOWN: "COMFY_DOWN", MSG_TIMEOUT: "TIMEOUT",
               MSG_GEN_FAILED: "GEN_FAILED", MSG_BAD_VERSION: "BAD_VERSION", MSG_BUSY: "BUSY", MSG_ID_USED: "ID_USED"}


def error_json(msg):
    return jsonify({"error": msg, "code": ERROR_CODES.get(msg, "")})


def friendly_generation_error(e):
    if isinstance(e, requests.ConnectionError):
        return MSG_COMFY_DOWN
    if isinstance(e, (TimeoutError, requests.Timeout)):
        return MSG_TIMEOUT
    return MSG_GEN_FAILED


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def current_session(participant_id):
    """该 ID 最近一次 start 之后的会话信息（从日志恢复）；从未开始过则返回 None"""
    events = [r for r in read_csv(EVENT_LOG) if r.get("participant_id") == participant_id]
    starts = [r for r in events if r.get("event") == "start"]
    if not starts:
        return None
    started = starts[-1]["timestamp"]
    later = [r for r in events if r["timestamp"] >= started]
    generations = [
        r for r in read_csv(GENERATION_LOG)
        if r.get("participant_id") == participant_id and r["timestamp"] >= started
        and r.get("version") and not r.get("error")
    ]
    finals = [r for r in later if r.get("event") == "final_choice" and r.get("version")]
    # 按时间顺序重放，得到"下一次修改基于哪一版"（base_version，0 表示下一句是新生成）：
    #   生成/修改成功 → 基于这张新图
    #   restart（最初から作り直す）→ 下一句新生成；restart_cancel → 回到最新一张
    #   base_change（从旧版本继续修改）→ 基于所选的那一版
    # 同一秒内生成排在事件前面（事件只可能发生在那次生成结束之后）
    steps = [(r["timestamp"], 0, "generation", int(r["version"])) for r in generations]
    steps += [(r["timestamp"], 1, r["event"], int(r["version"] or 0)) for r in later
              if r.get("event") in ("restart", "restart_cancel", "base_change")]
    base_version, pending_restart, latest = 0, False, 0
    for _, _, kind, version in sorted(steps, key=lambda x: x[:2]):
        if kind == "generation":
            base_version, pending_restart, latest = version, False, version
        elif kind == "restart":
            base_version, pending_restart = 0, True
        elif kind == "restart_cancel":
            base_version, pending_restart = latest, False
        elif kind == "base_change":
            base_version, pending_restart = version, False
    return {
        "started": started,
        "generations": generations,
        "final_version": int(finals[-1]["version"]) if finals else 0,
        "finished": any(r.get("event") in ("finish", "reset") for r in later),
        "pending_restart": pending_restart,
        "base_version": base_version,
    }


def session_base_path(participant_id):
    """本次会话中下一次修改的基准图（通常是最新一张，也可能是参加者选回的旧版本）；
    尚无图片或选择了"作り直す"时返回 None"""
    session = current_session(participant_id)
    if session is None:
        latest = max(existing_versions(participant_id), default=0)
        return image_path(participant_id, latest) if latest else None
    path = image_path(participant_id, session["base_version"])
    return path if session["base_version"] and os.path.exists(path) else None


def path_version(path):
    """从图片路径取版本号（ID_v番号.png）；没有则返回空字符串"""
    m = re.search(r"_v(\d+)\.png$", path or "")
    return int(m.group(1)) if m else ""


def image_path(participant_id, version):
    return os.path.join(IMAGE_DIR, participant_id, f"{participant_id}_v{version}.png")


def append_csv_row(file_path, headers, row):
    """如果 CSV 不存在则写入表头，然后追加一行；每次立即落盘"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file_exists = os.path.exists(file_path)
    if file_exists:
        # 表头增加了新列（例：seed）时，把旧文件升级为新表头（旧行的新列留空，不丢数据）
        with open(file_path, encoding="utf-8-sig", newline="") as f:
            old_rows = list(csv.DictReader(f))
            old_headers = list(old_rows[0].keys()) if old_rows else None
        if old_headers is not None and old_headers != headers and set(old_headers) <= set(headers):
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(old_rows)

    with open(file_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def log_event(event, version="", detail=""):
    append_csv_row(EVENT_LOG, EVENT_HEADERS, {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "participant_id": state["participant_id"] or "",
        "event": event,
        "version": version,
        "detail": detail,
    })


def save_image_bytes(image_bytes, participant_id, version):
    """保存图片，文件名带参加者ID和版本号，返回文件路径"""
    folder = os.path.join(IMAGE_DIR, participant_id)
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, f"{participant_id}_v{version}.png")
    with open(file_path, "wb") as f:
        f.write(image_bytes)
    return file_path


def existing_versions(participant_id):
    """已保存的该参加者图片的版本号列表（文件名 ID_v番号.png）"""
    folder = os.path.join(IMAGE_DIR, participant_id)
    if not os.path.isdir(folder):
        return []
    pattern = re.compile(r"^" + re.escape(participant_id) + r"_v(\d+)\.png$")
    return sorted(int(m.group(1)) for m in map(pattern.match, os.listdir(folder)) if m)


def ensure_participant(data):
    """确认请求中的参加者就是后端当前记住的参加者。

    后端重启、被重置或被别的会话顶掉时，用前端发来的 ID 从已保存的图片中恢复：
    版本号接着最大值往后编，修改基于最新一张图。调用方需持有 state_lock。
    返回参加者 ID；无法确定时返回 None。
    """
    participant_id = safe_id(data.get("participant_id"))
    if not participant_id:
        return state["participant_id"]
    if state["participant_id"] == participant_id:
        state["last_active"] = time.time()
        return participant_id
    if someone_else_active(participant_id):
        return None  # 别人正在进行：不切走会话

    previous = state["participant_id"] or ""
    # 版本号接着所有已存图片的最大值往后编（不覆盖）；
    # 修改的基准只取"本次会话"生成的最新一张，不会误用同一 ID 上一次会话的图
    latest = max(existing_versions(participant_id), default=0)
    latest_path = session_base_path(participant_id)
    state.update(participant_id=participant_id, version=latest, latest_image_path=latest_path,
                 last_active=time.time())
    log_event("restore", version=latest or "", detail=f"previous={previous}")
    print(f"RESTORE: participant {participant_id} (latest version {latest}, previous state {previous or 'none'})")
    return participant_id


@app.route("/")
def index():
    if not os.path.exists(os.path.join(FRONTEND_DIST, "index.html")):
        return "frontend/dist not found. Run: cd frontend && npm install && npm run build", 404
    return app.send_static_file("index.html")


@app.route("/api/health")
def health():
    """前端开始页用：确认后端和 ComfyUI 都能用"""
    try:
        comfy_ok = requests.get(f"{COMFY_URL}/system_stats", timeout=3).status_code == 200
    except requests.RequestException:
        comfy_ok = False
    return jsonify({"backend": True, "comfyui": comfy_ok})


@app.route("/api/busy", methods=["POST"])
def busy():
    """开始页"下一步"时先确认：是否有别的参加者正在进行（不写日志）"""
    data = request.get_json(silent=True) or {}
    participant_id = safe_id(normalize_id(data.get("participant_id")))
    with state_lock:
        return jsonify({"busy": someone_else_active(participant_id),
                        "used": id_already_used(participant_id)})


@app.route("/api/start", methods=["POST"])
def start_participant():
    """开始新的参加者：设置ID并清空上一个人的状态"""
    data = request.get_json(silent=True) or {}
    raw = normalize_id(data.get("participant_id"))
    participant_id = safe_id(raw)

    if not raw:
        return error_json(MSG_NO_ID), 400
    if participant_id != raw:
        # 含有平假名、汉字、符号等无法用于文件名的字符时，不偷偷删掉，而是请对方重新输入
        return error_json(MSG_BAD_ID), 400

    with state_lock:
        if id_already_used(participant_id):
            print(f"ID USED: {participant_id} was already used, start refused")
            return error_json(MSG_ID_USED), 409
        if someone_else_active(participant_id):
            print(f"BUSY: {participant_id} tried to start while {state['participant_id']} is active")
            return error_json(MSG_BUSY), 409
        # 同一个 ID 再次开始时，版本号接着已有的最大值往后编，避免覆盖之前的图片；
        # 但下一句仍按"新生成"处理（不基于旧图修改）
        latest = max(existing_versions(participant_id), default=0)
        state.update(participant_id=participant_id, version=latest, latest_image_path=None,
                     last_active=time.time())
        log_event("start", detail=f"numbering_continues_after=v{latest}" if latest else "")

    print(f"START: participant {participant_id} (existing versions up to {latest})")
    return jsonify({"message": "started", "participant_id": participant_id})


@app.route("/api/generate", methods=["POST"])
def generate_character():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()

    if not message:
        return error_json(MSG_NO_MESSAGE), 400

    with state_lock:
        participant_id = ensure_participant(data)
        if not participant_id:
            return error_json(MSG_NO_SESSION), 400

        is_edit = state["latest_image_path"] is not None
        base_version = path_version(state["latest_image_path"]) if is_edit else ""
        version = state["version"] + 1
        started = time.time()
        error = ""
        image_file = ""
        # 改写：沿用基准版本的种子（构图保持）；全文没变或旧数据没有种子时换新种子
        base = version_record(participant_id, base_version) if is_edit else None
        if base and base.get("seed") and base.get("prompt", "").strip() != message:
            seed = int(base["seed"])
        else:
            seed = new_seed()

        try:
            image_bytes = comfy_text_to_image(message, seed)
            reply = "修正しました。" if is_edit else "生成しました。"

            path = save_image_bytes(image_bytes, participant_id, version)
            image_file = os.path.relpath(path, BASE_DIR)
            state["latest_image_path"] = path
            state["version"] = version
            image_url = "data:image/png;base64," + base64.b64encode(image_bytes).decode()
            response = jsonify({"reply": reply, "image": image_url, "version": version,
                                "action": "rewrite" if is_edit else "generate"})
        except Exception as e:
            print("ERROR:", e)
            error = f"{type(e).__name__}: {e}"  # 日志里保留技术细节
            response = (error_json(friendly_generation_error(e)), 500)
        finally:
            # 每次生成立刻写日志（包括出错）
            append_csv_row(GENERATION_LOG, GENERATION_HEADERS, {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "participant_id": participant_id,
                "version": version if not error else "",
                "action": "rewrite" if is_edit else "generate",
                "base_version": base_version,
                "prompt": message,
                "input_language": detect_language(message),
                "duration_sec": round(time.time() - started, 2),
                "image_file": image_file,
                "error": error,
                "seed": seed,
            })

    return response


@app.route("/api/final", methods=["POST"])
def choose_final():
    """记录参加者选定的最终图片版本（用于和纸质问卷核对）"""
    data = request.get_json(silent=True) or {}
    version = data.get("version")

    with state_lock:
        if not ensure_participant(data):
            return error_json(MSG_NO_SESSION), 400
        if not isinstance(version, int) or not 1 <= version <= state["version"]:
            return error_json(MSG_BAD_VERSION), 400
        log_event("final_choice", version=version)

    return jsonify({"message": "final choice saved", "version": version})


@app.route("/api/restart", methods=["POST"])
def restart_design():
    """"最初から作り直す"：下一句不再基于上一张图修改，而是重新生成（之前的版本保留，仍可选为最终图片）。
    cancel=true 时取消，恢复为基于最新一张修改。"""
    data = request.get_json(silent=True) or {}
    cancel = bool(data.get("cancel"))

    with state_lock:
        participant_id = ensure_participant(data)
        if not participant_id:
            return error_json(MSG_NO_SESSION), 400
        if cancel:
            log_event("restart_cancel")
            state["latest_image_path"] = session_base_path(participant_id)
        else:
            log_event("restart", detail=f"after_v{state['version']}")
            state["latest_image_path"] = None

        base = path_version(state["latest_image_path"]) or 0

    return jsonify({"message": "ok", "pending_restart": not cancel, "base_version": base})


@app.route("/api/base", methods=["POST"])
def choose_base():
    """从旧版本继续修改：下一次修改基于参加者选的那一版（必须是本次会话生成的图）"""
    data = request.get_json(silent=True) or {}
    version = data.get("version")

    with state_lock:
        participant_id = ensure_participant(data)
        if not participant_id:
            return error_json(MSG_NO_SESSION), 400
        session = current_session(participant_id)
        own = {int(r["version"]) for r in session["generations"]} if session else set()
        if not isinstance(version, int) or version not in own                 or not os.path.exists(image_path(participant_id, version)):
            return error_json(MSG_BAD_VERSION), 400
        log_event("base_change", version=version)
        state["latest_image_path"] = image_path(participant_id, version)

    return jsonify({"message": "ok", "base_version": version})


@app.route("/api/resume", methods=["POST"])
def resume_session():
    """页面刷新（或误关标签页）后恢复本次会话：已生成的版本、最终选择、已经过的时间。

    生成进行中刷新时，这里会等那次生成结束（同一把锁）再返回，所以结果里包含它。
    """
    data = request.get_json(silent=True) or {}
    participant_id = safe_id(data.get("participant_id"))
    if not participant_id:
        return error_json(MSG_NO_SESSION), 400

    with state_lock:
        session = current_session(participant_id)
        if session is None or session["finished"]:
            return jsonify({"active": False})
        if someone_else_active(participant_id):
            return jsonify({"active": False, "busy": True})
        ensure_participant(data)
        items = [
            {
                "version": int(r["version"]),
                "action": r["action"],
                "prompt": r["prompt"],
                "image": f"/api/image/{participant_id}/{r['version']}",
            }
            for r in session["generations"]
            if os.path.exists(image_path(participant_id, r["version"]))
        ]
        elapsed = (datetime.now() - datetime.fromisoformat(session["started"])).total_seconds()
        log_event("resume", version=items[-1]["version"] if items else "",
                  detail=f"elapsed_sec={int(elapsed)}")

    print(f"RESUME: participant {participant_id} ({len(items)} versions, {int(elapsed)}s elapsed)")
    return jsonify({
        "active": True,
        "participant_id": participant_id,
        "elapsed_sec": max(int(elapsed), 0),
        "final_version": session["final_version"],
        "pending_restart": session["pending_restart"],
        "base_version": session["base_version"],
        "items": items,
    })


@app.route("/api/image/<participant_id>/<int:version>")
def get_image(participant_id, version):
    """恢复会话时取回已保存的图片"""
    participant_id = safe_id(participant_id)
    folder = os.path.join(IMAGE_DIR, participant_id)
    return send_from_directory(folder, f"{participant_id}_v{version}.png", max_age=0)


@app.route("/api/ping", methods=["POST"])
def ping():
    """前端在进行中每 30 秒发一次：表示"这个人还在"（不写日志）"""
    data = request.get_json(silent=True) or {}
    with state_lock:
        ok = ensure_participant(data)
    return (jsonify({"message": "ok"}), 200) if ok else (error_json(MSG_BUSY), 409)


@app.route("/api/event", methods=["POST"])
def client_event():
    """前端上报的事件：time_warning / time_up / finish，以及 ui_language（界面语言，detail 为 ja/zh/en）"""
    data = request.get_json(silent=True) or {}
    event = str(data.get("event", ""))[:40]
    if event not in {"time_warning", "time_up", "finish", "ui_language", "pre_experience", "pre_clarity"}:
        return jsonify({"error": "unknown event"}), 400

    with state_lock:
        if not ensure_participant(data):
            return error_json(MSG_NO_SESSION), 400
        detail = str(data.get("detail", ""))[:200]
        if event in {"pre_experience", "pre_clarity"} and detail not in {"1", "2", "3", "4", "5"}:
            return jsonify({"error": "bad answer"}), 400
        log_event(event, detail=detail)

    return jsonify({"message": "ok"})


@app.route("/api/survey", methods=["POST"])
def submit_survey():
    """线上参加者的问卷。结束（reset）之后才提交，所以不依赖当前状态，按前端发来的 ID 记录"""
    data = request.get_json(silent=True) or {}
    raw = normalize_id(data.get("participant_id"))
    participant_id = safe_id(raw)
    if not raw or participant_id != raw:
        return error_json(MSG_BAD_ID), 400
    answers = data.get("answers") or {}

    def scale(key):  # 1〜5，未回答は空
        value = answers.get(key)
        return value if isinstance(value, int) and 1 <= value <= 5 else ""

    def choices(key, limit=None):
        picked = [c for c in answers.get(key) or [] if c in SURVEY_CHOICES[key]]
        picked = list(dict.fromkeys(picked))  # 重複を除く（順序は保つ）
        if "none" in picked and len(picked) > 1:  # 「特になし」と他は両立しない
            picked.remove("none")
        return ";".join(picked[:limit] if limit else picked)

    def text(key):
        return str(answers.get(key) or "").replace("\r", " ").strip()[:1000]

    final_version = data.get("final_version")
    append_csv_row(SURVEY_LOG, SURVEY_HEADERS, {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "participant_id": participant_id,
        "final_version": final_version if isinstance(final_version, int) and final_version > 0 else "",
        "ui_language": str(data.get("lang", ""))[:5],
        "mode": "web",  # 紙のアンケートを入力するときは paper
        "clearer": scale("qc"),
        "satisfaction": scale("q3"),
        "focus": choices("q4", limit=3),
        "focus_other": text("q4_other"),
        "difficulty": choices("q5"),
        "difficulty_other": text("q5_other"),
        "reason": choices("q6"),
        "reason_other": text("q6_other"),
        "comment": text("q7"),
    })
    print(f"SURVEY: saved for participant {participant_id}")
    return jsonify({"message": "ok"})


@app.route("/api/reset", methods=["POST"])
def reset_character():
    """清空当前参加者的状态（下一个人开始前）"""
    with state_lock:
        if state["participant_id"]:
            log_event("reset")
        state.update(participant_id=None, version=0, latest_image_path=None, last_active=0.0)

    print("RESET OK: participant state cleared")
    return jsonify({"message": "reset ok"})


def warm_up():
    """启动后先生成一张丢弃的图，让模型提前载入显存，第一位参加者不用等加载"""
    try:
        comfy_text_to_image("a simple blue circle icon", 1)
        print("WARMUP: done")
    except Exception as e:
        print("WARMUP failed (ignored):", e)


if __name__ == "__main__":
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    debug = os.getenv("FLASK_DEBUG") == "1"
    # 默认只监听本机；远程访问通过 Tailscale（tailscale serve）转发进来
    host = os.getenv("HOST", "127.0.0.1")
    if os.getenv("WARMUP", "1") == "1" and (not debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true"):
        threading.Thread(target=warm_up, daemon=True).start()
    app.run(host=host, port=5000, debug=debug)
