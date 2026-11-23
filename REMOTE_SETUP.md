# 现场用 Mac 远程使用家里的 PC

思路：**所有东西（ComfyUI、后端、网页、日志）都跑在家里的 PC 上**，现场的 Mac 只用浏览器打开网址。
PC 和 Mac 之间用 Tailscale 连接（免费，不用改路由器端口）。

## 一次性准备（在家里做，现场前一定要试一遍）

1. **PC 和 Mac 都安装 Tailscale**，用同一个账号登录（https://tailscale.com/download）。
2. **PC 设置不休眠**：设置 → 系统 → 电源 → 接通电源时，"使屏幕和睡眠进入睡眠状态"都设为"从不"。
   实验当天 PC 要一直插电、开机、联网。
3. 在 PC 上第一次运行：

   ```
   pip install -r backend\requirements.txt
   ```

4. 在 PC 上用管理员 PowerShell 运行一次，把本机 5000 端口通过 Tailscale 发布出去：

   ```
   tailscale serve --bg 5000
   ```

   运行后会显示一个形如 `https://<电脑名>.<xxxx>.ts.net` 的地址（第一次可能要在 Tailscale 管理页面打开 HTTPS 功能，
   按提示点链接即可）。这个地址只有登录了你的 Tailscale 账号的设备才能访问。
5. 在 Mac 上用浏览器打开上面的地址，看到"準備OK"就说明通了。

## 实验当天

1. 在家里的 PC 上双击 `start_experiment.cmd`（会自动启动 ComfyUI、网页和后端，并预热模型）。
   看到 `WARMUP: done` 后再出门；到现场后不需要再碰 PC。
2. 现场 Mac 的 Tailscale 保持开启，浏览器打开步骤 4 的地址。
3. 每位参加者：输入参加者ID → 体验 →"最终画像"选 Ver. → 点"終了して次の人へ"。

## 数据在哪里（都在家里 PC 上）

- 日志：`backend\logs\generation_log.csv`、`backend\logs\event_log.csv`
- 线上参加者的问卷（问题 3〜8）：`backend\logs\survey_log.csv`（结束后的感谢画面里展开填写；选项保存为代码，含义见 `frontend\src\survey.js`；`mode` 列为 `web`）
- 问题 1・2（AI 使用经验、开始前想法的清晰度）：所有人都在开始时于画面上回答，记在 `backend\logs\event_log.csv` 的 `pre_experience` / `pre_clarity`（detail = 1〜5）
- 现场纸质问卷按桌面 `预备实验\纸质问卷录入\` 的模板录入（`mode` = `paper`），可以和 survey_log 直接合并
- 图片：`backend\generated_images\<参加者ID>\<参加者ID>_v<版本>.png`

这些都含参加者数据，已在 `.gitignore` 里，**不要提交到仓库**。实验结束后记得拷走并备份。

## 现场出问题时

| 现象 | 处理 |
| --- | --- |
| 开始页显示"サーバーに接続できません" | Mac 的 Tailscale 没开 / 家里 PC 断网或休眠了 |
| 显示"画像生成エンジンに接続できません" | PC 上的 ComfyUI 没在运行，重新运行 `start_experiment.cmd` |
| 生成特别慢 | 现场网络慢；图片约 1MB，一般 10 秒内能回来 |
| 页面被刷新 | 倒计时和当前画面会丢，但已生成的图和日志都在 PC 上；让参加者用**同一个ID**重新开始（版本号会从 1 重新计） |

## 建议

- 出发前，用手机热点连接 Mac，完整走一遍流程，确认在"不同网络"下也能用。
- 家里有人的话，请对方不要关 PC 或断网。
- 想完全不依赖网络，就把 PC 带到现场（同样运行 `start_experiment.cmd`，在 PC 上打开 `http://127.0.0.1:5000`）。
