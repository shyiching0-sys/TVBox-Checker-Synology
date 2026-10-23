# 📺 TVBox-Checker-Synology
> 專為群暉 NAS Docker 環境打造的 TVBox 影視站點配置/直播源快速驗證與一鍵過濾匯出完全體工具。

[![Docker Compatible](https://shields.io)](https://synology.com)
[![Python](https://shields.io)](https://python.org)
[![License](https://shields.io)](LICENSE)

本項目採用 **Python + Flask + Gunicorn** 實現，針對群暉 NAS (DSM) 本地內網環境進行了深度底層優化。採用**「零外置網頁依賴、純內存直讀」**架構，專門適配影視爬蟲 JSON 的 `api_site` 站點配置結構，具備極高的抗堵塞與抗卡死性能。

---

## ✨ 核心特性 (Features)

* 🚀 **智能深度解析**：精準相容 TVBox 影視配置中的 `api_site` 結構，自動抓取「愛奇藝」、「豆瓣」、「茅臺資源」等數十個影視爬蟲站點的 API 網址。
* ⚡ **多線程極速測速**：後端採用 `ThreadPoolExecutor` 開啟 16 執行緒併發同步測速，效率極高。
* 🛡️ **強效抗堵塞機制**：每個網絡請求強制 **1.5秒超時切斷**。即使遇到嚴重死鎖或失效的線路，背景也絕不堵塞，網頁絕不卡死。
* 📦 **零外置網頁依賴 (No-JS Freeze)**：將前端 HTML 結構完全硬編碼嵌入 Python 背景內存中，無需外置 `templates/` 資料夾。徹底免受瀏覽器大檔案渲染卡死與群暉全域變數命名衝突。
* 🌐 **群暉 Host 網絡直通**：默認採用 `network_mode: host`，直接共享 NAS 本地網卡，通訊速度提升 10 倍，徹底根除 Docker 虛擬網橋延遲。
* 📥 **一鍵打包導出**：自動篩選測試狀態為「可用 (200)」的站點，純後端在記憶體中重組並以**二進位檔案流 (Attachment Stream)** 甩給瀏覽器下載，秒級生成最乾淨、無失效線路的新 JSON 文件。

---

## 🛠️ 群暉 NAS 極速部署 (Deployment)

本項目已優化為**最治本、最不可能出錯的原地直讀部署模式**。請透過 SSH 連線您的群暉 NAS，並執行以下一鍵部署命令：

```bash
# 1. 建立並進入項目資料夾
mkdir -p /volume1/docker/tvbox-checker && cd /volume1/docker/tvbox-checker
mkdir -p data

# 2. 將本倉庫的 app.py 下載或寫入到該目錄下

# 3. 強制洗牌舊快取並直接拉取純淨環境原地啟動
docker rm -f tvbox-checker 2>/dev/null
docker run -d \
  --name tvbox-checker \
  --network host \
  --restart always \
  -v /volume1/docker/tvbox-checker/app.py:/app/app.py \
  -v /volume1/docker/tvbox-checker/data:/app/data \
  -w /app \
  python:3.11-slim \
  sh -c "pip install --no-cache-dir Flask==3.0.2 requests==2.31.0 gunicorn==21.2.0 && python app.py"
```

---

## 💡 使用指南 (Usage)

1. **訪問網頁**：打開瀏覽器，強烈建議開啟 **「無痕分頁（隱私模式）」**（防止瀏覽器快取舊網頁），訪問 `http://[您的群暉NAS內網IP]:5000`。
2. **匯入大檔案**：點擊綠色的 **「📁 點擊選取電腦內的 .json 檔案」** 按鈕，選取您的 16KB JSON 配置。檔案內容將被秒級填入文字方框中。
3. **開始批量驗證**：點擊紅色的 **「🚀 開始批量驗證」** 按鈕，右側會實時重新整理並動態跳出所有站點的延遲、狀態與評分。
4. **打包匯出**：當 78/78（或您的站點總數）驗證完成後，右上角會自動解凍彈出藍色的 **「📥 一鍵打包下載乾淨的 JSON 檔案」** 按鈕。點擊即可秒級下載已剔除全部失效線路、只保留 100% 滿分可用線路的全新配置檔案。

---

## 📂 目錄結構說明 (Structure)

```text
/volume1/docker/tvbox-checker/
├── app.py          # 核心後端邏輯 + 前端內存網頁整合體 (完全體版本)
└── data/           # 數據掛載目錄 (選填，用於本地擴展儲存)
```

## 📄 開源協議 (License)

本項目基於 **MIT License** 協議開源。歡迎提交 Issue 或 Pull Request 共同優化！
