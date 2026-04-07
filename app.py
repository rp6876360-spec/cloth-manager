import streamlit as st
import os
import uuid
import io
import base64
import json
import cv2
import numpy as np
import database
from PIL import Image
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

# 初始化
database.init_db()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Flask API
app = Flask(__name__)
CORS(app)

CATEGORIES = ["上装", "下装", "鞋子", "帽子", "首饰", "其他配饰"]


@app.route('/api/clothes', methods=['GET'])
def get_clothes():
    """获取所有衣服"""
    clothes = database.get_all_clothes()
    result = []
    for c in clothes:
        result.append({
            "id": c[0],
            "image_path": c[1],
            "season": c[2],
            "category": c[3],
            "keywords": c[4],
            "created_at": str(c[5]) if c[5] else None
        })
    return jsonify(result)


@app.route('/api/image/<path:image_path>', methods=['GET'])
def get_image(image_path):
    """获取图片"""
    try:
        return send_file(image_path)
    except:
        return send_file(image_path.replace('/', '\\'))


@app.route('/api/upload', methods=['POST'])
def upload():
    """上传衣服"""
    file = request.files.get('file')
    season = request.form.get('season')
    category = request.form.get('category')
    keywords = request.form.get('keywords', '')
    remove_bg = request.form.get('remove_bg', 'false') == 'true'

    if not file or not season or not category:
        return jsonify({"error": "缺少参数"}), 400

    # 读取图片
    bytes_data = file.read()
    nparr = np.frombuffer(bytes_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 抠图
    if remove_bg:
        try:
            from rembg import remove
            pil_img = Image.fromarray(img)
            buf = io.BytesIO()
            pil_img.save(buf, format='PNG')
            buf.seek(0)
            pil_img = Image.open(buf)
            result = remove(pil_img)
            img = np.array(result)
        except Exception as e:
            print(f"抠图失败: {e}")

    # 保存
    if len(img.shape) == 3 and img.shape[2] == 4:
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGBA2BGRA)
    else:
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    fn = f"{uuid.uuid4()}.png"
    path = os.path.join(UPLOAD_DIR, fn)
    cv2.imwrite(path, img_bgr)

    database.add_cloth(path, season, category, keywords)

    return jsonify({"success": True, "path": path})


@app.route('/api/clothes/<int:cloth_id>', methods=['DELETE'])
def delete_cloth(cloth_id):
    """删除衣服"""
    database.delete_cloth(cloth_id)
    return jsonify({"success": True})


def run_streamlit():
    """运行Streamlit界面"""
    st.set_page_config(page_title="衣服管理助手", page_icon="👔", layout="wide")

    st.markdown("""
    <style>
        section[data-testid="stMain"] { background: #F0F0F0; }
    </style>
    """, unsafe_allow_html=True)

    st.title("👔 衣服管理助手")
    st.markdown("### 请使用前端界面访问")
    st.code("cd frontend && npm run dev", language="bash")
    st.markdown("前端地址: http://localhost:5173")


if __name__ == '__main__':
    import threading
    import sys

    # 在后台线程运行Flask API
    def run_flask():
        app.run(host='0.0.0.0', port=8501, debug=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    print("=" * 50)
    print("🚀 服务已启动:")
    print("   API: http://localhost:8501")
    print("   前端: cd frontend && npm run dev")
    print("=" * 50)

    # 运行Streamlit
    run_streamlit()
