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
            with st.spinner("处理中..."):
                bytes_data = uploaded.getvalue()
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
                        result = remove(pil_img)
                        img = np.array(result)
                    except Exception as e:
                        st.error(f"抠图失败: {e}")

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

    # 统一大小滑块
    img_size = st.slider("统一调整大小", 80, 250, 150)

    st.markdown("---")

    # 选择衣服
    cols = st.columns(3)
    selections = {}

    for i, cat in enumerate(CATEGORIES):
        with cols[i % 3]:
            items = clothes_by[cat]
            if items:
                options = ["不选"] + [f"{c[4] or '无'}" for c in items]
                choice = st.selectbox(f"{CATEGORY_ICONS[cat]} {cat}", options, key=f"sel_{cat}")
                if choice != "不选":
                    idx = options.index(choice) - 1
                    selections[cat] = items[idx]

    # 显示搭配
    st.markdown("---")
    st.subheader("搭配效果")

    if selections:
        cols = st.columns(len(selections))
        for i, (cat, cloth) in enumerate(selections.items()):
            with cols[i]:
                if os.path.exists(cloth[1]):
                    # 调整大小
                    img = cv2.imread(cloth[1], cv2.IMREAD_UNCHANGED)
                    h, w = img.shape[:2]
                    scale = img_size / max(h, w)
                    new_w, new_h = int(w * scale), int(h * scale)
                    resized = cv2.resize(img, (new_w, new_h))
                    _, buf = cv2.imencode('.png', resized)
                    b64 = base64.b64encode(buf).decode()
                    st.markdown(f'<img src="data:image/png;base64,{b64}" style="display:block; margin:0 auto;">', unsafe_allow_html=True)
                    st.caption(f"{CATEGORY_ICONS[cat]} {cat}")
    else:
        st.info("从上方选择衣服进行搭配")