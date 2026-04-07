import streamlit as st
import os
import uuid
import io
import base64
import cv2
import numpy as np
import database
from PIL import Image

# 页面配置
st.set_page_config(page_title="衣服管理助手", page_icon="👔", layout="wide")

# CSS
st.markdown("""
<style>
    section[data-testid="stMain"] { background: #F0F0F0; }
    h1, h2, h3, p, div, label, span { color: #1A1A1A !important; }
    section[data-testid="stSidebar"] { background: #1A1A1A; }
    section[data-testid="stSidebar"] h2 { color: white !important; }
    .stTextInput input { background: white !important; color: #1A1A1A !important; }
    .stButton > button { background: white !important; color: #1A1A1A !important; border: 1px solid #CCC !important; }
</style>
""", unsafe_allow_html=True)

# 初始化
database.init_db()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

CATEGORIES = ["上装", "下装", "鞋子", "帽子", "首饰", "其他配饰"]
CATEGORY_ICONS = {"上装": "👕", "下装": "👖", "鞋子": "👟", "帽子": "🧢", "首饰": "📿", "其他配饰": "🎒"}

# 侧边栏
st.sidebar.markdown("<h2>衣服管理</h2>", unsafe_allow_html=True)

if "nav" not in st.session_state:
    st.session_state.nav = "上传衣服"

if st.sidebar.button("📤 上传衣服", use_container_width=True):
    st.session_state.nav = "上传衣服"
if st.sidebar.button("👚 浏览衣服", use_container_width=True):
    st.session_state.nav = "浏览衣服"
if st.sidebar.button("✨ 搭配", use_container_width=True):
    st.session_state.nav = "搭配"

page = st.session_state.nav


# ===== 上传 =====
if page == "上传衣服":
    st.title("📤 上传衣服")

    uploaded = st.file_uploader("选择图片", type=["jpg", "jpeg", "png"])

    if uploaded:
        st.write(f"已选择: {uploaded.name}")

        s = st.selectbox("季节", ["春秋装", "夏装", "冬装"])
        cat = st.selectbox("类型", CATEGORIES)
        kw = st.text_input("关键词", placeholder="蓝色、休闲")
        remove_bg = st.checkbox("✂️ 自动抠图")

        if st.button("💾 保存"):
            with st.spinner("处理中，请稍候..."):
                bytes_data = uploaded.getvalue()

                # 用OpenCV读取
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
                        st.error(f"抠图失败: {e}")

                # 保存
                if len(img.shape) == 3 and img.shape[2] == 4:
                    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGBA2BGRA)
                else:
                    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                fn = f"{uuid.uuid4()}.png"
                path = os.path.join(UPLOAD_DIR, fn)
                cv2.imwrite(path, img_bgr)

                database.add_cloth(path, s, cat, kw)
                st.success("保存成功!")

# ===== 浏览 =====
elif page == "浏览衣服":
    st.title("👚 我的衣橱")

    col1, col2, col3 = st.columns(3)
    with col1:
        fs = st.selectbox("季节", ["全部", "春秋装", "夏装", "冬装"])
    with col2:
        fc = st.selectbox("类型", ["全部"] + CATEGORIES)
    with col3:
        fk = st.text_input("搜索", placeholder="关键词...")

    clothes = database.get_clothes_by_filter(fs, fc, fk)
    st.write(f"共 {len(clothes)} 件")

    if clothes:
        cols = st.columns(4)
        for i, c in enumerate(clothes):
            with cols[i % 4]:
                if os.path.exists(c[1]):
                    with open(c[1], "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    st.markdown(f'<img src="data:image/png;base64,{b64}" style="width:100%;">', unsafe_allow_html=True)
                st.write(f"{c[2]} {c[3]}")
                if c[4]:
                    st.caption(c[4])
                if st.button("删除", key=f"del_{c[0]}"):
                    database.delete_cloth(c[0])
                    st.rerun()
    else:
        st.info("还没有衣服")

# ===== 搭配 =====
elif page == "搭配":
    st.title("✨ 搭配")

    clothes_by = {cat: database.get_clothes_by_category(cat) for cat in CATEGORIES}

    # 初始化
    if "outfit_items" not in st.session_state:
        st.session_state.outfit_items = []

    # 获取所有衣服的图片base64
    def get_image_b64(path):
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return None

    # 添加衣服到搭配
    st.markdown("### 📋 添加衣服到搭配")

    # 分成两行显示
    row1 = ["上装", "下装", "鞋子"]
    row2 = ["帽子", "首饰", "其他配饰"]

    for row_cats in [row1, row2]:
        cols = st.columns(3)
        for j, cat in enumerate(row_cats):
            with cols[j]:
                items = clothes_by[cat]
                if items:
                    options = ["选择..."] + [f"{c[4] or '无关键词'}" for c in items]
                    choice = st.selectbox(f"{CATEGORY_ICONS[cat]} {cat}", options, key=f"add_{cat}")
                    if choice != "选择...":
                        idx = options.index(choice) - 1
                        cloth = items[idx]
                        b64 = get_image_b64(cloth[1])
                        if b64:
                            # 检查是否已添加
                            existing = [i for i, x in enumerate(st.session_state.outfit_items) if x["cloth_id"] == cloth[0]]
                            if not existing:
                                st.session_state.outfit_items.append({
                                    "cloth_id": cloth[0],
                                    "category": cat,
                                    "icon": CATEGORY_ICONS[cat],
                                    "image": b64,
                                    "x": 30 + len(st.session_state.outfit_items) * 50,
                                    "y": 30 + len(st.session_state.outfit_items) * 30,
                                    "width": 80
                                })
                                st.success(f"已添加 {cat}")

    # 显示搭配画布
    st.markdown("---")
    st.markdown("### 🎨 搭配画布（拖拽移动，滑块调整大小）")

    if st.session_state.outfit_items:
        if st.button("🗑️ 清空全部"):
            st.session_state.outfit_items = []
            st.rerun()

        # 滑块调整大小
        st.markdown("**调整大小**")
        cols = st.columns(min(len(st.session_state.outfit_items), 6))
        for i, item in enumerate(st.session_state.outfit_items):
            with cols[i % 6]:
                new_width = st.slider(f"{item['icon']}", 40, 150, item["width"], key=f"w_{item['cloth_id']}")
                if new_width != item["width"]:
                    st.session_state.outfit_items[i]["width"] = new_width

        # 拖拽画布
        items_html = ""
        for i, item in enumerate(st.session_state.outfit_items):
            items_html += f'''
            <div class="item" id="item_{i}" style="position:absolute; left:{item['x']}px; top:{item['y']}px; width:{item['width']}px; cursor:move; user-select:none;">
                <img src="data:image/png;base64,{item['image']}" style="width:100%; pointer-events:none; border:1px solid #ddd; border-radius:4px;">
            </div>
            '''

        st.markdown(f"""
        <div id="canvas" style="position:relative; width:100%; height:350px; background:linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius:12px; border:2px solid #ccc; overflow:hidden;">
            {items_html}
        </div>
        <script>
        (function(){{
            const canvas = document.getElementById('canvas');
            let drag = null, startX, startY, startLeft, startTop;

            canvas.addEventListener('mousedown', function(e) {{
                const item = e.target.closest('.item');
                if(item) {{
                    drag = item;
                    const rect = item.getBoundingClientRect();
                    startX = e.clientX;
                    startY = e.clientY;
                    startLeft = item.offsetLeft;
                    startTop = item.offsetTop;
                    item.style.zIndex = 100;
                }}
            }});

            document.addEventListener('mousemove', function(e) {{
                if(drag) {{
                    const dx = e.clientX - startX;
                    const dy = e.clientY - startY;
                    let newLeft = startLeft + dx;
                    let newTop = startTop + dy;
                    newLeft = Math.max(0, Math.min(newLeft, canvas.offsetWidth - drag.offsetWidth));
                    newTop = Math.max(0, Math.min(newTop, canvas.offsetHeight - drag.offsetHeight));
                    drag.style.left = newLeft + 'px';
                    drag.style.top = newTop + 'px';
                }}
            }});

            document.addEventListener('mouseup', function(e) {{
                if(drag) {{
                    drag.style.zIndex = '';
                    drag = null;
                }}
            }});
        }})();
        </script>
        """, unsafe_allow_html=True)

        # 移除按钮
        st.markdown("**移除衣服**")
        cols = st.columns(min(len(st.session_state.outfit_items), 6))
        for i, item in enumerate(st.session_state.outfit_items):
            with cols[i % 6]:
                if st.button(f"移除 {item['icon']}", key=f"rm_{item['cloth_id']}"):
                    st.session_state.outfit_items.pop(i)
                    st.rerun()

    else:
        st.info("从上方选择衣服添加到搭配画布")