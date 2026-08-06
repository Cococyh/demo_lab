# 对话型虚拟角色生成 Demo

Vue + Flask + OpenAI 图像 API 构建的课堂测试网站。用户通过对话生成并连续修改虚拟角色，网站同时收集每张图片评分和体验问卷。

## 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

在 `.env` 中填写 `OPENAI_API_KEY`，然后启动：

```bash
python app.py
```

默认采用适合课堂测试的快速配置：`gpt-image-2`、`1024x1024`、`low`、JPEG 85%。如果更重视画质，可在 `.env` 中把 `OPENAI_IMAGE_QUALITY` 改为 `medium`。

## 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认访问 `http://127.0.0.1:5000`。部署到其他地址时，设置：

```bash
VITE_API_BASE_URL=https://your-api.example.com
```

## 本次测试版优化

- 使用低质量方形草稿缩短图像生成时间。
- JPEG 压缩减少后端响应体积和浏览器内存占用。
- 生成期间保留上一版本，并显示经过时间和当前阶段。
- 每位测试者拥有独立会话，支持多人同时测试。
- 自动记录每次生成耗时和平均耗时，随问卷一起写入 CSV。
