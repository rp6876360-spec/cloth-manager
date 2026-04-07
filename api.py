import os
import sys
import cv2
import numpy as np
from PIL import Image
import io
import uuid
import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from collections import Counter

# 初始化
import database
database.init_db()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)


def crop_transparent(img):
    """裁切透明边框，只保留有效内容"""
    if len(img.shape) == 3 and img.shape[2] == 4:
        alpha = img[:, :, 3]
        coords = cv2.findNonZero(alpha)
        if coords is not None:
            x, y, w, h = cv2.boundingRect(coords)
            return img[y:y+h, x:x+w]
    return img


def extract_dominant_color(img, k=3):
    """提取主色调"""
    try:
        # 如果是RGBA，转为RGB
        if len(img.shape) == 3 and img.shape[2] == 4:
            # 只取非透明区域
            alpha = img[:, :, 3]
            mask = alpha > 10
            if mask.sum() > 0:
                img = img[mask].reshape(-1, 3)
            else:
                img = img[:, :, :3].reshape(-1, 3)
        else:
            img = img.reshape(-1, 3)

        # K-means聚类找主色
        img = np.float32(img)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(img, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        # 找出最多的颜色
        label_counts = Counter(labels.flatten())
        dominant_label = label_counts.most_common(1)[0][0]
        dominant_color = centers[dominant_label]

        # 转换为颜色名称
        return rgb_to_color_name(dominant_color)
    except:
        return "未知"


def rgb_to_color_name(rgb):
    """RGB转颜色名称"""
    r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])

    # 简单的颜色分类
    if r > 200 and g > 200 and b > 200:
        return "白色"
    elif r < 30 and g < 30 and b < 30:
        return "黑色"
    elif r > 200 and g < 100 and b < 100:
        return "红色"
    elif r < 100 and g > 150 and b < 100:
        return "绿色"
    elif r < 100 and g < 100 and b > 180:
        return "蓝色"
    elif r > 200 and g > 200 and b < 100:
        return "黄色"
    elif r > 200 and g > 100 and b < 100:
        return "橙色"
    elif r > 150 and g < 100 and b > 150:
        return "紫色"
    elif r > 200 and g < 150 and b < 150:
        return "粉色"
    elif r < 100 and g > 150 and b > 150:
        return "青色"
    elif r > 150 and g > 100 and b < 80:
        return "棕色"
    elif 100 < r < 200 and 100 < g < 200 and 100 < b < 200:
        return "灰色"
    elif r > g and r > b:
        return "红色系"
    elif g > r and g > b:
        return "绿色系"
    elif b > r and b > g:
        return "蓝色系"
    else:
        return "中性色"


def detect_style(img, keywords=""):
    """检测衣服风格"""
    keywords_lower = keywords.lower() if keywords else ""

    # 基于关键词判断
    style_keywords = {
        "正式": ["西装", "正装", "衬衫", "商务", "职业", "ol"],
        "休闲": ["休闲", "t恤", "卫衣", "牛仔", "运动", "t恤", "t桖"],
        "运动": ["运动", "健身", "跑步", "瑜伽", "运动服"],
        "街头": ["街头", "潮牌", "嘻哈", "oversize"],
        "优雅": ["连衣裙", "裙子", "优雅", "淑女", "蕾丝"],
        "简约": ["简约", "基础款", "纯色", "素色"]
    }

    for style, kws in style_keywords.items():
        for kw in kws:
            if kw in keywords_lower:
                return style

    # 默认返回休闲
    return "休闲"


def get_shopping_suggestions():
    """获取购物建议"""
    stats = database.get_statistics()
    suggestions = []

    category = stats.get('category', {})
    total = stats.get('total_count', 0)

    if total == 0:
        return ["开始添加衣服吧！"]

    # 分析各类型比例
    expected_ratio = {
        "上装": 0.35,
        "下装": 0.25,
        "鞋子": 0.15,
        "帽子": 0.05,
        "首饰": 0.10,
        "其他配饰": 0.10
    }

    for cat, ratio in expected_ratio.items():
        count = category.get(cat, 0)
        expected = total * ratio
        if count < expected * 0.5:  # 少于预期的一半
            suggestions.append(f"缺少{cat}：建议添加{int(expected - count)}件")

    if not suggestions:
        suggestions.append("衣柜搭配很均衡！")

    return suggestions


@app.route('/api/clothes', methods=['GET'])
def get_clothes():
    clothes = database.get_all_clothes()
    result = [{
        'id': c[0],
        'image_path': c[1],
        'season': c[2],
        'category': c[3],
        'keywords': c[4],
        'brand': c[5] if len(c) > 5 else None,
        'price': c[6] if len(c) > 6 else None,
        'style': c[7] if len(c) > 7 else None,
        'color': c[8] if len(c) > 8 else None
    } for c in clothes]
    return jsonify(result)


@app.route('/api/image/<path:image_path>', methods=['GET'])
def get_image(image_path):
    try:
        return send_file(image_path)
    except:
        return send_file(image_path.replace('/', '\\'))


@app.route('/api/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    season = request.form.get('season')
    category = request.form.get('category')
    keywords = request.form.get('keywords', '')
    remove_bg = request.form.get('remove_bg', 'false') == 'true'
    brand = request.form.get('brand', '')
    price = request.form.get('price', '')

    if not file:
        return jsonify({'error': 'no file'}), 400

    bytes_data = file.read()
    nparr = np.frombuffer(bytes_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    original_img = img.copy()

    if remove_bg:
        try:
            from rembg import remove
            pil_img = Image.fromarray(img)
            buf = io.BytesIO()
            pil_img.save(buf, format='PNG')
            buf.seek(0)
            pil_img = Image.open(buf)
            img = np.array(remove(pil_img))
            img = crop_transparent(img)
        except: pass

    # 自动识别颜色和风格
    color = extract_dominant_color(original_img)
    style = detect_style(original_img, keywords)

    # 处理价格
    try:
        price_val = float(price) if price else None
    except:
        price_val = None

    if len(img.shape) == 3 and img.shape[2] == 4:
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGBA2BGRA)
    else:
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    fn = f'{uuid.uuid4()}.png'
    path = os.path.join(UPLOAD_DIR, fn)
    cv2.imwrite(path, img_bgr)

    database.add_cloth(path, season, category, keywords, brand or None, price_val, style, color)

    return jsonify({
        'success': True,
        'path': path,
        'color': color,
        'style': style
    })


@app.route('/api/clothes/<int:cloth_id>', methods=['DELETE'])
def delete_cloth(cloth_id):
    database.delete_cloth(cloth_id)
    return jsonify({'success': True})


# 统计API
@app.route('/api/statistics', methods=['GET'])
def get_stats():
    stats = database.get_statistics()
    stats['suggestions'] = get_shopping_suggestions()
    return jsonify(stats)


# 搭配相关API
@app.route('/api/outfits', methods=['GET'])
def get_outfits():
    outfits = database.get_all_outfits()
    result = [{'id': o[0], 'name': o[1], 'items': o[2], 'created_at': str(o[3]) if o[3] else None} for o in outfits]
    return jsonify(result)


@app.route('/api/outfits', methods=['POST'])
def save_outfit():
    data = request.json
    name = data.get('name', '未命名搭配')
    items = json.dumps(data.get('items', []))
    database.save_outfit(name, items)
    return jsonify({'success': True})


@app.route('/api/outfits/<int:outfit_id>', methods=['DELETE'])
def delete_outfit(outfit_id):
    database.delete_outfit(outfit_id)
    return jsonify({'success': True})


if __name__ == '__main__':
    print("=" * 50)
    print("API running on http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
