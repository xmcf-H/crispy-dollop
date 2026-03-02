# app.py - Flask后端 + AI调用核心逻辑
from flask import Flask, request, jsonify, render_template
import json
import os
import requests
from prompt import prompt_pe_unauth, prompt_unauth  # 导入Prompt模板

# ========== 配置项（只需要改这里！）==========
GEMINI_API_KEY = "1"  # Google Gemini API Key
GEMINI_API_URL = "h11"  # Gemini API URL
PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
}  # 代理设置（如果不需要代理，设置为None或删除此配置）
# ==========================================

app = Flask(__name__)

# 核心函数：调用Gemini AI接口
def call_ai(prompt, input_data):
    """
    调用AI模型，传入Prompt和检测数据，返回AI分析结果
    """
    try:
        # 构造完整的提示词
        full_prompt = f"{prompt}\n\n请分析以下数据：\n{json.dumps(input_data, ensure_ascii=False)}"
        
        # 构造请求数据
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": full_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1
            }
        }
        
        # 构造请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        # 构造API URL
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        # 添加调试信息
        print(f"[DEBUG] 使用的URL: {url}")
        
        # 调用Gemini API，添加超时设置和代理
        response = requests.post(url, json=payload, headers=headers, timeout=30, proxies=PROXIES)
        
        # 检查响应状态
        response.raise_for_status()
        
        # 提取AI返回的内容
        response_data = response.json()
        ai_content = response_data["candidates"][0]["content"]["parts"][0]["text"]
        
        # 尝试解析为JSON
        try:
            return json.loads(ai_content)
        except:
            # 如果不是JSON格式，返回一个包含文本的结果
            return {
                "result": "unknown",
                "analysis": ai_content
            }
    except Exception as e:
        # 出错时返回错误信息
        error_message = f"调用AI失败：{str(e)}"
        # 添加更多调试信息
        if 'response' in locals():
            error_message += f"，状态码：{response.status_code}，响应内容：{response.text[:500] if len(response.text) > 500 else response.text}"
        return {
            "result": "unknown",
            "analysis": error_message
        }

# 路由1：首页（展示前端页面）
@app.route("/")
def index():
    try:
        return render_template("index.html")
    except Exception as e:
        return f"Error: {str(e)}"

# 路由2：越权漏洞检测接口（供前端调用）
@app.route("/detect/pe_unauth", methods=["POST"])
def detect_pe_unauth():
    # 获取前端传的参数
    data = request.get_json()
    # 构造AI需要的输入数据
    input_data = {
        "reqA": data.get("reqA"),
        "responseA": data.get("responseA"),
        "responseB": data.get("responseB"),
        "statusB": data.get("statusB")
    }
    # 调用AI分析
    ai_result = call_ai(prompt_pe_unauth, input_data)
    # 返回结果给前端
    return jsonify({
        "code": 0,
        "data": ai_result
    })

# 路由3：未授权漏洞检测接口
@app.route("/detect/unauth", methods=["POST"])
def detect_unauth():
    data = request.get_json()
    input_data = {
        "reqA": data.get("reqA"),
        "responseA": data.get("responseA"),
        "responseB": data.get("responseB"),
        "statusB": data.get("statusB")
    }
    ai_result = call_ai(prompt_unauth, input_data)
    return jsonify({
        "code": 0,
        "data": ai_result
    })

# 启动服务
if __name__ == "__main__":
    print(f"使用的GEMINI_API_URL: {GEMINI_API_URL}")
    app.run(debug=False, host="0.0.0.0", port=5000)
