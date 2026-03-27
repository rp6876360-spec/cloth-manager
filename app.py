import streamlit as st
import os
import uuid
from PIL import Image
import io
import database
from rembg import remove

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
    .stButton button { background: white !important; color: #1A1A1A !important; border: 1px solid #CCC !important; }
    .stCaption { color: #555 !important; }
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

    c1, c2 = st.columns([1, 1], gap="large")

    with c1:
        uploaded = st.file_uploader("选择图片", type=["jpg", "jpeg", "png"])
        if uploaded:
            # 读取bytes并创建新的Image对象
            bytes_data = uploaded.getvalue()
            img = Image.open(io.BytesIO(bytes_data))
            img = Image.frombytes(img.mode, img.size, img.tobytes())
            st.image(img, use_container_width=True)

    with c2:
        if uploaded:
            with st.form("form", clear_on_submit=True):
                s = st.selectbox("季节", ["春秋装", "夏装", "冬装"])
                cat = st.selectbox("类型", CATEGORIES)
                kw = st.text_input("关键词", placeholder="蓝色、休闲")
                remove_bg = st.checkbox("✂️ 自动抠图（去除背景）", value=False)

                if st.form_submit_button("💾 保存", use_container_width=True):
                    with st.spinner("处理中..."):
                        # 从bytes重新创建图片
                        img_process = Image.open(io.BytesIO(bytes_data))
                        img_process = Image.frombytes(img_process.mode, img_process.size, img_process.tobytes())

                        if remove_bg:
                            img_process = remove(img_process)
                            if img_process.mode != "RGB":
                                img_process = img_process.convert("RGB")
                        else:
                            if img_process.mode in ("RGBA", "P"):
                                img_process = img_process.convert("RGB")

                        fn = f"{uuid.uuid4()}.png"
                        path = os.path.join(UPLOAD_DIR, fn)
                        img_process.save(path, "PNG")
                        database.add_cloth(path, s, cat, kw)
                    st.success("保存成功!")

# ===== 浏览 =====
elif page == "浏览衣服":
    st.title("👚 我的衣橱")

    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
    with col1:
        fs = st.selectbox("季节", ["全部", "春秋装", "夏装", "冬装"])
    with col2:
        fc = st.selectbox("类型", ["全部"] + CATEGORIES)
    with col3:
        fk = st.text_input("搜索", placeholder="输入关键词...")
    with col4:
        if st.button("🔄 重置"):
            st.rerun()

    clothes = database.get_clothes_by_filter(fs, fc, fk)
    st.write(f"**共 {len(clothes)} 件**")

    if clothes:
        cols = st.columns(4, gap="large")
        for i, c in enumerate(clothes):
            with cols[i % 4]:
                if os.path.exists(c[1]):
                    st.image(c[1], use_container_width=True)
                st.write(f"**{c[2]} {c[3]}**")
                if c[4]:
                    st.caption(f"🏷️ {c[4]}")
                if st.button(f"🗑️ 删除", key=f"del_{c[0]}"):
                    database.delete_cloth(c[0])
                    st.rerun()
    else:
        st.info("还没有衣服，去上传页面添加吧")

# ===== 搭配 =====
elif page == "搭配":
    st.title("✨ 搭配")

    clothes_by = {cat: database.get_clothes_by_category(cat) for cat in CATEGORIES}

    c1, c2, c3 = st.columns(3)
    sel = {}
    with c1:
        t = ["不选"] + [f"{c[2]} | {c[4] or '-'}" for c in clothes_by["上装"]] if clothes_by["上装"] else []
        sel["上装"] = st.selectbox("👕 上装", t) if t else st.warning("暂无上装")
    with c2:
        t = ["不选"] + [f"{c[2]} | {c[4] or '-'}" for c in clothes_by["下装"]] if clothes_by["下装"] else []
        sel["下装"] = st.selectbox("👖 下装", t) if t else st.warning("暂无下装")
    with c3:
        t = ["不选"] + [f"{c[2]} | {c[4] or '-'}" for c in clothes_by["鞋子"]] if clothes_by["鞋子"] else []
        sel["鞋子"] = st.selectbox("👟 鞋子", t) if t else st.warning("暂无鞋子")

    c4, c5, c6 = st.columns(3)
    with c4:
        t = ["不选"] + [f"{c[2]} | {c[4] or '-'}" for c in clothes_by["帽子"]] if clothes_by["帽子"] else []
        sel["帽子"] = st.selectbox("🧢 帽子", t) if t else st.warning("暂无帽子")
    with c5:
        t = ["不选"] + [f"{c[2]} | {c[4] or '-'}" for c in clothes_by["首饰"]] if clothes_by["首饰"] else []
        sel["首饰"] = st.selectbox("📿 首饰", t) if t else st.warning("暂无首饰")
    with c6:
        t = ["不选"] + [f"{c[2]} | {c[4] or '-'}" for c in clothes_by["其他配饰"]] if clothes_by["其他配饰"] else []
        sel["其他配饰"] = st.selectbox("🎒 配饰", t) if t else st.warning("暂无配饰")

    has_sel = any(v and v != "不选" for v in sel.values() if v)

    if has_sel:
        st.markdown("---")
        st.subheader("🎉 搭配效果")

        items = []
        for cat, s in sel.items():
            if s and s != "不选":
                for c in clothes_by[cat]:
                    if f"{c[2]} | {c[4] or '-'}" == s:
                        items.append((CATEGORY_ICONS[cat], c, cat))
                        break

        items.sort(key=lambda x: CATEGORIES.index(x[2]) if x[2] in CATEGORIES else 999)

        if items:
            cols = st.columns(len(items))
            for i, (ic, cl, ct) in enumerate(items):
                with cols[i]:
                    if os.path.exists(cl[1]):
                        st.image(cl[1], caption=f"{ic} {ct}", use_container_width=True)

        kws = [c[4] for _, c, _ in items if c[4]]
        if kws:
            st.write(f"**关键词**: {' + '.join(kws)}")
