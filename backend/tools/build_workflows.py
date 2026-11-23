"""根据 ComfyUI 自带的 Qwen Image 2.1 官方 Turbo 模板，生成网站后端使用的 API 格式工作流。

用法（在 backend 目录下）：
    python tools/build_workflows.py

所有模型名与采样参数都从官方模板中读取，只有下面 OVERRIDES 里写明的项目与官方不同。
官方模板默认关闭的"提示词扩写"（Prompt Enhancer）不放进来：参加者写的原话直接交给模型。
"""
import json
import os
import sys

TEMPLATE_DIR = os.environ.get(
    "COMFY_TEMPLATE_DIR",
    r"E:\AI\ComfyUI_windows_portable\python_embeded\Lib\site-packages\comfyui_workflow_templates_json\templates",
)
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workflows")

# 与官方模板不同的地方（只有这些）
OVERRIDES = {
    # 竖图 2:3、约 157 万像素（官方默认 1024x1024 正方形；边长取 32 的倍数）。
    # 2026-11-11 与 864x1152 对比后改用：细节稍多、修改更彻底，修改耗时约 17 秒（864x1152 约 11 秒）
    "width": 1024,
    "height": 1536,
}


def load_template(name):
    with open(os.path.join(TEMPLATE_DIR, name + ".json"), encoding="utf-8") as f:
        data = json.load(f)
    subgraph = data["definitions"]["subgraphs"][0]
    wrapper = next(n for n in data["nodes"] if n["type"] == subgraph["id"])
    # 外层子图节点上暴露的参数（实际生效的值）
    exposed = dict(zip([i["name"] for i in subgraph["inputs"]], wrapper["widgets_values"]))
    nodes = {n["type"]: n for n in subgraph["nodes"] if n["type"] != "CLIPLoader" or "qwen3vl" in str(n.get("widgets_values"))}
    return exposed, nodes


def widget(nodes, node_type, index=0):
    return nodes[node_type]["widgets_values"][index]


def common(exposed, nodes):
    """两种工作流共用的部分：模型加载、缓存、采样器、噪声表、解码。"""
    return {
        "unet": {"class_type": "UNETLoader",
                 "inputs": {"unet_name": exposed["unet_name"], "weight_dtype": widget(nodes, "UNETLoader", 1)}},
        "clip": {"class_type": "CLIPLoader",
                 "inputs": {"clip_name": exposed["clip_name"], "type": widget(nodes, "CLIPLoader", 1),
                            "device": widget(nodes, "CLIPLoader", 2)}},
        "vae": {"class_type": "VAELoader", "inputs": {"vae_name": exposed["vae_name"]}},
        "cache": {"class_type": "QwenImage21Cache",
                  "inputs": {"model": ["unet", 0], "device": exposed.get("device", "auto"),
                             "dtype": exposed.get("dtype", exposed.get("dtype_1", "default"))}},
        "noise": {"class_type": "RandomNoise", "inputs": {"noise_seed": 0}},  # 每次由后端随机设置
        "sampler_select": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": exposed["scheduler"]}},
        "sigmas": {"class_type": "ManualSigmas", "inputs": {"sigmas": widget(nodes, "ManualSigmas")}},
        "guider": {"class_type": "CFGGuider",
                   "inputs": {"model": ["cache", 0], "positive": ["encode", 0], "negative": ["encode", 1],
                              "cfg": float(exposed.get("cfg", widget(nodes, "CFGGuider")))}},
        "decode": {"class_type": "VAEDecode", "inputs": {"samples": ["sample", 0], "vae": ["vae", 0]}},
        "save": {"class_type": "SaveImage", "inputs": {"images": ["decode", 0], "filename_prefix": "demo_lab/qwen21_turbo"}},
    }


def build_text_to_image():
    exposed, nodes = load_template("image_qwen_image_2_1_turbo_t2i")
    wf = common(exposed, nodes)
    wf["encode"] = {"class_type": "TextEncodeQwenImage21",
                    "inputs": {"clip": ["clip", 0], "prompt": "", "negative_prompt": exposed["negative_prompt"],
                               "resolution": widget(nodes, "TextEncodeQwenImage21", 2)}}
    wf["latent"] = {"class_type": "EmptyLatentImage",
                    "inputs": {"width": OVERRIDES["width"], "height": OVERRIDES["height"], "batch_size": 1}}
    wf["sample"] = {"class_type": "SamplerCustomAdvanced",
                    "inputs": {"noise": ["noise", 0], "guider": ["guider", 0], "sampler": ["sampler_select", 0],
                               "sigmas": ["sigmas", 0], "latent_image": ["latent", 0]}}
    return wf


def build_image_edit():
    exposed, nodes = load_template("image_qwen_image_2_1_turbo_image_edit")
    wf = common(exposed, nodes)
    wf["load_image"] = {"class_type": "LoadImage", "inputs": {"image": ""}}  # 由后端设为上一张图
    wf["encode"] = {"class_type": "TextEncodeQwenImage21",
                    "inputs": {"clip": ["clip", 0], "prompt": "", "negative_prompt": exposed["negative_prompt"],
                               "vae": ["vae", 0], "resolution": int(exposed["resolution"]),
                               "images.image_1": ["load_image", 0]}}
    # 官方模板 custom_size 关闭时，画布来自编码器输出的潜空间（与参考图同尺寸）
    assert str(exposed["switch"]) in ("False", "false"), "official template expects canvas from the encoder latent"
    wf["sample"] = {"class_type": "SamplerCustomAdvanced",
                    "inputs": {"noise": ["noise", 0], "guider": ["guider", 0], "sampler": ["sampler_select", 0],
                               "sigmas": ["sigmas", 0], "latent_image": ["encode", 2]}}
    return wf


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, wf in (("text_to_image_api.json", build_text_to_image()),
                     ("reference_edit_api.json", build_image_edit())):
        with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
            json.dump(wf, f, ensure_ascii=False, indent=2)
        print("wrote", name)
        for key in ("unet", "clip", "vae", "sampler_select", "sigmas", "guider", "encode"):
            shown = {k: v for k, v in wf[key]["inputs"].items() if not isinstance(v, list)}
            print(f"  {key:15} {shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
