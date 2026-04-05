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

    # 选择器
    col1, col2, col3 = st.columns(3)
    sel = {}

    with col1:
        tops = clothes_by["上装"]
        if tops:
            options = ["选择上装..."] + [f"{i+1}. {c[4] or '无关键词'}" for i, c in enumerate(tops)]
            sel["上装"] = st.selectbox("👕 上装", options)
        else:
            st.info("暂无上装")
            sel["上装"] = None

    with col2:
        bottoms = clothes_by["下装"]
        if bottoms:
            options = ["选择下装..."] + [f"{i+1}. {c[4] or '无关键词'}" for i, c in enumerate(bottoms)]
            sel["下装"] = st.selectbox("👖 下装", options)
        else:
            st.info("暂无下装")
            sel["下装"] = None

    with col3:
        shoes = clothes_by["鞋子"]
        if shoes:
            options = ["选择鞋子..."] + [f"{i+1}. {c[4] or '无关键词'}" for i, c in enumerate(shoes)]
            sel["鞋子"] = st.selectbox("👟 鞋子", options)
        else:
            st.info("暂无鞋子")
            sel["鞋子"] = None

    col4, col5, col6 = st.columns(3)
    with col4:
        hats = clothes_by["帽子"]
        if hats:
            options = ["选择帽子..."] + [f"{i+1}. {c[4] or '无关键词'}" for i, c in enumerate(hats)]
            sel["帽子"] = st.selectbox("🧢 帽子", options)
        else:
            sel["帽子"] = None

    with col5:
        jewelry = clothes_by["首饰"]
        if jewelry:
            options = ["选择首饰..."] + [f"{i+1}. {c[4] or '无关键词'}" for i, c in enumerate(jewelry)]
            sel["首饰"] = st.selectbox("📿 首饰", options)
        else:
            sel["首饰"] = None

    with col6:
        accs = clothes_by["其他配饰"]
        if accs:
            options = ["选择配饰..."] + [f"{i+1}. {c[4] or '无关键词'}" for i, c in enumerate(accs)]
            sel["其他配饰"] = st.selectbox("🎒 配饰", options)
        else:
            sel["其他配饰"] = None

    # 显示搭配结果
    st.markdown("---")
    st.subheader("搭配效果")

    # 收集选中的衣服
    selected = []
    for cat, choice in sel.items():
        if choice and not choice.startswith("选择"):
            idx = int(choice.split(".")[0]) - 1
            selected.append((CATEGORY_ICONS[cat], clothes_by[cat][idx], cat))

    if selected:
        cols = st.columns(len(selected))
        for i, (icon, cloth, cat) in enumerate(selected):
            with cols[i]:
                if os.path.exists(cloth[1]):
                    with open(cloth[1], "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    st.markdown(f'<img src="data:image/png;base64,{b64}" style="width:100%;">', unsafe_allow_html=True)
                    st.caption(f"{icon} {cat}")
    else:
        st.info("请选择衣服进行搭配")
