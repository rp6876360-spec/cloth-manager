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

@app.route('/api/clothes', methods=['GET'])
def get_clothes():
    clothes = database.get_all_clothes()
    result = [{'id': c[0], 'image_path': c[1], 'season': c[2], 'category': c[3], 'keywords': c[4]} for c in clothes]
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

    if not file:
        return jsonify({'error': 'no file'}), 400

    bytes_data = file.read()
    nparr = np.frombuffer(bytes_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    if remove_bg:
        try:
            from rembg import remove
            pil_img = Image.fromarray(img)
            buf = io.BytesIO()
            pil_img.save(buf, format='PNG')
            buf.seek(0)
            pil_img = Image.open(buf)
            img = np.array(remove(pil_img))
            # 裁切空白区域
            img = crop_transparent(img)
        except: pass

    if len(img.shape) == 3 and img.shape[2] == 4:
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGBA2BGRA)
    else:
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    fn = f'{uuid.uuid4()}.png'
    path = os.path.join(UPLOAD_DIR, fn)
    cv2.imwrite(path, img_bgr)
    database.add_cloth(path, season, category, keywords)
    return jsonify({'success': True, 'path': path})

@app.route('/api/clothes/<int:cloth_id>', methods=['DELETE'])
def delete_cloth(cloth_id):
    database.delete_cloth(cloth_id)
    return jsonify({'success': True})


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
    print("API running on http://localhost:8501")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
