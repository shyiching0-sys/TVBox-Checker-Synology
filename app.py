import os, json, time, concurrent.futures, requests, threading
from flask import Flask, jsonify, request, Response

app = Flask(__name__)
test_status = {"is_running": False, "total": 0, "current": 0, "results": []}
# 記憶原始輸入的完整 JSON 結構，以便匯出時保留非 api_site 的其餘全域配置
original_json_data = {}

def verify_single_url(name, url, key_id):
    start_time = time.time()
    try:
        res = requests.head(url, timeout=1.5, allow_redirects=True)
        if res.status_code >= 400: res = requests.get(url, timeout=1.5, stream=True)
        elapsed = (time.time() - start_time) * 1000
        if res.status_code == 200:
            score = max(50, 100 - int(elapsed / 50))
            return {"name": name, "url": url, "key_id": key_id, "status": "可用", "code": res.status_code, "delay": f"{elapsed:.0f}ms", "score": score, "style": "bg-ok"}
    except: pass
    return {"name": name, "url": url, "key_id": key_id, "status": "失效", "code": "Timeout", "delay": "-", "score": 0, "style": "bg-fail"}

def parse_source_text(raw_data):
    global original_json_data
    source_list = []
    raw_data = raw_data.strip()
    if not raw_data: return []
    if raw_data.startswith('{') or raw_data.startswith('['):
        try:
            parsed = json.loads(raw_data)
            original_json_data = parsed # 深度備份
            if isinstance(parsed, dict) and "api_site" in parsed:
                for k, item in parsed["api_site"].items():
                    if isinstance(item, dict) and "api" in item:
                        source_list.append({"name": item.get("name", k), "url": item.get("api", ""), "key_id": k})
                return [s for s in source_list if s["url"]]
        except: pass
    return []

@app.route('/')
def index():
    return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>TVBox 驗證工具</title>
    <style>
        body { background:#f4f6f9; font-family:sans-serif; padding:20px; color:#333; }
        .row { display:flex; gap:20px; } .card { background:white; padding:20px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.05); flex:1; }
        .btn-success { background:#198754; color:white; border:none; padding:8px 15px; border-radius:4px; font-weight:bold; cursor:pointer; margin-bottom:10px; }
        .btn-danger { background:#dc3545; color:white; border:none; padding:12px 20px; border-radius:4px; font-weight:bold; cursor:pointer; width:100%; margin-top:15px; }
        .btn-export { background:#0d6efd; color:white; border:none; padding:6px 12px; border-radius:4px; font-weight:bold; cursor:pointer; display:none; }
        table { width:100%; border-collapse:collapse; margin-top:15px; font-size:14px; } th, td { padding:10px; border-bottom:1px solid #eee; text-align:left; }
        .bg-ok { background:#d1e7dd; color:#0f5132; } .bg-fail { background:#f8d7da; color:#842029; }
    </style></head><body>
    <h2>📺 TVBox 站點配置快速驗證工具 (完全體過濾匯出版)</h2>
    <div class="row"><div class="card">
        <h3>📂 導入配置</h3>
        <button class="btn-success" onclick="document.getElementById('fi').click()">📁 點擊選取電腦內的 .json 檔案</button>
        <input type="file" id="fi" style="display:none;" accept=".json" onchange="loadFile(this)">
        <p style="color:#6c757d; font-size:13px; margin-top:5px;" id="st">或者直接將 16KB JSON 內容貼入下方方框：</p>
        <textarea id="tx" style="width:100%; height:200px; font-family:monospace;" placeholder="請在此處貼上您的 api_site 配置 JSON..."></textarea>
        <button class="btn-danger" onclick="run()" id="btn">🚀 開始批量驗證</button>
    </div><div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3>📋 驗證結果 (<span id="pg">0 / 0</span>)</h3>
            <!-- 🚀 新增一鍵匯出乾淨新 JSON 按鈕，完全走純後端檔案流下載，絕不卡死 -->
            <button class="btn-export" id="exBtn" onclick="exportCleanJson()">📥 一鍵打包下載乾淨的 JSON 檔案</button>
        </div>
        <div style="max-height:400px; overflow-y:auto;">
            <table><thead><tr><th>名稱與網址</th><th>狀態</th><th>延遲</th><th>評分</th></tr></thead><tbody id="tb"></tbody></table>
        </div>
    </div></div>
    <script>
        let tm = null;
        function loadFile(input) {
            if (!input.files || input.files.length === 0) return;
            let file = input.files[0]; let reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById("tx").value = e.target.result;
                document.getElementById("st").innerText = "📄 已載入檔案：" + file.name + " (" + (file.size/1024).toFixed(1) + " KB)";
                document.getElementById("st").style.color = "#198754";
            }; reader.readAsText(file);
        }
        function run() {
            let txt = document.getElementById("tx").value; if(!txt.trim()) { alert("請先貼入內容或選取檔案！"); return; }
            document.getElementById("btn").disabled = true; document.getElementById("exBtn").style.display = "none";
            let fd = new FormData(); fd.append("threads", "16"); fd.append("sources", txt);
            fetch("/upload_and_test", { method: "POST", body: fd }).then(res => res.json()).then(data => {
                if(data.status === "success") { tm = setInterval(chk, 1000); } else { alert(data.message); document.getElementById("btn").disabled = false; }
            });
        }
        function chk() {
            fetch("/progress?t=" + new Date().getTime()).then(res => res.json()).then(data => {
                document.getElementById("pg").innerText = data.current + " / " + data.total;
                if(data.results.length > 0) {
                    document.getElementById("tb").innerHTML = data.results.sort((a,b)=>b.score-a.score).map(i => `
                        <tr class="${i.style}"><td><b>${i.name}</b><br><small style="color:#6c757d;word-break:break-all;">${i.url}</small></td>
                        <td>${i.status} (${i.code})</td><td>${i.delay}</td><td>${i.score}</td></tr>
                    `).join("");
                }
                if(!data.is_running && data.current === data.total && data.total > 0) { 
                    clearInterval(tm); document.getElementById("btn").disabled = false; 
                    document.getElementById("exBtn").style.display = "block"; alert("驗證完成！已為您解鎖一鍵導出乾淨 JSON 功能。"); 
                }
            });
        }
        // 🚀 強大、不卡死的純後端導出跳轉
        function exportCleanJson() {
            window.location.href = "/export_clean_json";
        }
    </script></body></html>"""

@app.route('/upload_and_test', methods=['POST'])
def upload_and_test():
    global test_status
    if test_status["is_running"]: return jsonify({"status": "error", "message": "已有任務運行中"})
    raw_content = request.form.get("sources", "")
    s_list = parse_source_text(raw_content)
    if not s_list: return jsonify({"status": "error", "message": "未能成功抓取到有效 api_site 站點配置！"})
    test_status.update({"is_running": True, "total": len(s_list), "current": 0, "results": []})
    def run_pool():
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as exec:
            futures = {exec.submit(verify_single_url, item['name'], item['url'], item['key_id']): item for item in s_list}
            for f in concurrent.futures.as_completed(futures):
                test_status["results"].append(f.result())
                test_status["current"] += 1
        test_status["is_running"] = False
    threading.Thread(target=run_pool).start()
    return jsonify({"status": "success", "message": f"成功載入 {len(s_list)} 個影視站點，開始同步測速！"})

@app.route('/progress')
def progress(): return jsonify(test_status)

# 🚀 【不卡死核心】純後端二進位檔案流匯出：直接在記憶體中篩選過濾並輸出為附件下載
@app.route('/export_clean_json')
def export_clean_json():
    global test_status, original_json_data
    if not test_status["results"]:
        return "暫無檢測數據", 400
    
    # 提取所有測試狀態為「可用」的站點 key_id
    available_keys = {item["key_id"] for item in test_status["results"] if item["status"] == "可用"}
    
    # 建立一個乾淨的全新配置字典
    clean_json = {}
    
    # 1. 如果原始資料包含其他全域屬性（如 wallpaper, spider 等），完整保留
    if isinstance(original_json_data, dict):
        for k, v in original_json_data.items():
            if k != "api_site":
                clean_json[k] = v
                
        # 2. 精準過濾 api_site，只保留可用的站點
        if "api_site" in original_json_data:
            clean_json["api_site"] = {}
            for site_key, site_val in original_json_data["api_site"].items():
                if site_key in available_keys:
                    clean_json["api_site"][site_key] = site_val
    else:
        # 防禦機制：若原始非標準字典，則只重組可用站點
        clean_json["api_site"] = {}
        for item in test_status["results"]:
            if item["status"] == "可用":
                clean_json["api_site"][item["key_id"]] = {"name": item["name"], "api": item["url"]}

    # 將過濾後的乾淨結構序列化為美化的 JSON 格式字串
    output_json_str = json.dumps(clean_json, ensure_ascii=False, indent=2)
    
    # 直接以 Attachment 附件檔案流形式甩給瀏覽器，秒級下載，完全免去前端渲染卡死
    return Response(
        output_json_str,
        mimetype="application/json",
        headers={"Content-disposition": "attachment; filename=tvbox_clean_site.json"}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
