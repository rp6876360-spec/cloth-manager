import streamlit as st
import os
import uuid
from PIL import Image
import database

# 页面配置
st.set_page_config(page_title="衣服管理助手", page_icon="👔", layout="wide")

# Shadcn风格CSS - 改进版
st.markdown("""
<style>
    /* 全局 */
    .stApp {
        background: #FAFAFA;
    }

    /* 标题 */
    h1 {
        font-size: 1.75rem;
        font-weight: 600;
        color: #171717;
        margin-bottom: 1.5rem;
    }
    h3 {
        font-size: 1rem;
        font-weight: 600;
        color: #171717;
        margin-bottom: 1rem;
    }

    /* 卡片 */
    .card {
        background: white;
        border: 1px solid #E5E5E5;
        border-radius: 8px;
        padding: 1.25rem;
    }

    /* 按钮 */
    .stButton > button {
        background: white;
        border: 1px solid #D4D4D4;
        border-radius: 6px;
        color: #171717;
        font-size: 0.875rem;
        font-weight: 500;
        padding: 0.4rem 0.75rem;
    }
    .stButton > button:hover {
        background: #F5F5F5;
    }
    .stButton > button:active {
        background: #EBEBEB;
    }

    /* Primary按钮 */
    .primary-btn button {
        background: #171717;
        border-color: #171717;
        color: white;
    }
    .primary-btn button:hover {
        background: #404040;
    }

    /* 侧边栏 */
    [data-testid="stSidebar"] {
        background: #171717;
        padding: 1rem 0.5rem;
    }
    [data-testid="stSidebar"] h2 {
        color: white;
        font-size: 1.25rem;
        padding: 0 0.75rem 1rem;
        border-bottom: 1px solid #333;
        margin-bottom: 1rem;
    }
    [data-testid="stSidebar"] .stRadio > div {
        flex-direction: column;
        gap: 0.25rem;
    }
    [data-testid="stSidebar"] .stRadio > label {
        color: #A3A3A3 !important;
        font-size: 0.9rem;
        padding: 0.6rem 0.75rem;
        border-radius: 6px;
        margin: 0;
    }
    [data-testid="stSidebar"] .stRadio > label:hover {
        color: white !important;
        background: #262626;
    }
    [data-testid="stSidebar"] div[aria-checked="true"] > label {
        background: #404040 !important;
        color: white !important;
    }

    /* 标签 */
    .tag {
        display: inline-flex;
        padding: 0.2rem 0.6rem;
        font-size: 0.75rem;
        font-weight: 500;
        border-radius: 4px;
        margin-right: 0.25rem;
    }
    .tag-spring { background: #FEF3C7; color: #92400E; }
    .tag-summer { background: #DBEAFE; color: #1E40AF; }
    .tag-winter { background: #EDE9FE; color: #5B21B6; }
    .tag-top { background: #FEF3C7; color: #92400E; }
    .tag-bottom { background: #CFFAFE; color: #155E75; }
    .tag-shoes { background: #FFEDD5; color: #9A3412; }
    .tag-hat { background: #F3E8FF; color: #6B21A8; }
    .tag-jewelry { background: #FCE7F3; color: #9D174D; }
    .tag-accessory { background: #D1FAE5; color: #065F46; }

    /* 上传 */
    .upload-box {
        border: 1px dashed #A3A3A3;
        border-radius: 6px;
        padding: 2rem;
        text-align: center;
    }

    /* 筛选栏 */
    .filter-bar {
        background: white;
        border: 1px solid #E5E5E5;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
    }
    .filter-bar .stSelectbox > div > div {
        background: #FAFAFA;
    }

    /* 空状态 */
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: #737373;
    }
    .empty-state h3 {
        color: #171717;
    }
</style>
""", unsafe_allow_html=True)

# 初始化
database.init_db()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

CATEGORIES = ["上装", "下装", "鞋子", "帽子", "首饰", "其他配饰"]
CATEGORY_ICONS = {"上装": "👕", "下装": "👖", "鞋子": "👟", "帽子": "🧢", "首饰": "📿", "其他配饰": "🎒"}

# 侧边栏
st.sidebar.markdown("## 衣服管理")
page = st.sidebar.radio("", ["上传衣服", "浏览衣服", "搭配"], label_visibility="collapsed")

# ===== 上传 =====
if page == "上传衣服":
    st.title("上传衣服")

    c1, c2 = st.columns([1, 1], gap="medium")

    with c1:
        uploaded = st.file_uploader("选择图片", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if uploaded:
            img = Image.open(uploaded)
            st.image(img, use_container_width=True)

    with c2:
        if uploaded:
            with st.form("form", clear_on_submit=True):
                s = st.selectbox("季节", ["春秋装", "夏装", "冬装"])
                cat = st.selectbox("类型", CATEGORIES)
                kw = st.text_input("关键词", placeholder="蓝色、休闲")

                st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
                if st.form_submit_button("保存", use_container_width=True):
                    ext = uploaded.name.split('.')[-1]
                    fn = f"{uuid.uuid4()}.{ext}"
                    path = os.path.join(UPLOAD_DIR, fn)
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img.save(path)
                    database.add_cloth(path, s, cat, kw)
                    st.success("保存成功")
                st.markdown('</div>', unsafe_allow_html=True)

# ===== 浏览 =====
elif page == "浏览衣服":
    st.title("我的衣橱")

    # 筛选
    with st.container():
        st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([1, 1, 2, 1], gap="small")
        with c1:
            fs = st.selectbox("季节", ["全部", "春秋装", "夏装", "冬装"])
        with c2:
            fc = st.selectbox("类型", ["全部"] + CATEGORIES)
        with c3:
            fk = st.text_input("搜索", placeholder="关键词...", label_visibility="collapsed")
        with c4:
            if st.button("重置"):
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    clothes = database.get_clothes_by_filter(fs, fc, fk)
    st.caption(f"共 {len(clothes)} 件")

    if clothes:
        cols = st.columns(4, gap="medium")
        for i, c in enumerate(clothes):
            with cols[i % 4]:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                if os.path.exists(c[1]):
                    st.image(c[1], use_container_width=True)

                st_tag = "spring" if c[2] == "春秋装" else ("summer" if c[2] == "夏装" else "winter")
                cat_tag = {"上装": "top", "下装": "bottom", "鞋子": "shoes", "帽子": "hat", "首饰": "jewelry", "其他配饰": "accessory"}.get(c[3], "top")

                st.markdown(f'<span class="tag tag-{st_tag}">{c[2]}</span> <span class="tag tag-{cat_tag}">{c[3]}</span>', unsafe_allow_html=True)

                if c[4]:
                    st.caption(c[4])

                if st.button("删除", key=f"d_{c[0]}"):
                    database.delete_cloth(c[0])
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><h3>暂无衣服</h3><p>去上传添加吧</p></div>', unsafe_allow_html=True)

# ===== 搭配 =====
elif page == "搭配":
    st.title("搭配")

    clothes_by = {cat: database.get_clothes_by_category(cat) for cat in CATEGORIES}

    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            t = ["不选"] + [f"{c[2]} | {c[4] or '无'}" for c in clothes_by["上装"]] if clothes_by["上装"] else []
            sel = {}
            sel["上装"] = st.selectbox("👕 上装", t) if t else st.caption("暂无上装")
        with c2:
            t = ["不选"] + [f"{c[2]} | {c[4] or '无'}" for c in clothes_by["下装"]] if clothes_by["下装"] else []
            sel["下装"] = st.selectbox("👖 下装", t) if t else st.caption("暂无下装")
        with c3:
            t = ["不选"] + [f"{c[2]} | {c[4] or '无'}" for c in clothes_by["鞋子"]] if clothes_by["鞋子"] else []
            sel["鞋子"] = st.selectbox("👟 鞋子", t) if t else st.caption("暂无鞋子")

        c4, c5, c6 = st.columns(3, gap="medium")
        with c4:
            t = ["不选"] + [f"{c[2]} | {c[4] or '无'}" for c in clothes_by["帽子"]] if clothes_by["帽子"] else []
            sel["帽子"] = st.selectbox("🧢 帽子", t) if t else st.caption("暂无帽子")
        with c5:
            t = ["不选"] + [f"{c[2]} | {c[4] or '无'}" for c in clothes_by["首饰"]] if clothes_by["首饰"] else []
            sel["首饰"] = st.selectbox("📿 首饰", t) if t else st.caption("暂无首饰")
        with c6:
            t = ["不选"] + [f"{c[2]} | {c[4] or '无'}" for c in clothes_by["其他配饰"]] if clothes_by["其他配饰"] else []
            sel["其他配饰"] = st.selectbox("🎒 配饰", t) if t else st.caption("暂无配饰")
        st.markdown('</div>', unsafe_allow_html=True)

    has_sel = any(v and v != "不选" for v in sel.values() if v)

    if has_sel:
        st.markdown('<div class="card" style="margin-top: 1rem;">', unsafe_allow_html=True)
        st.markdown("#### 搭配效果")

        items = []
        for cat, s in sel.items():
            if s and s != "不选":
                for c in clothes_by[cat]:
                    if f"{c[2]} | {c[4] or '无'}" == s:
                        items.append((CATEGORY_ICONS[cat], c, cat))
                        break

        items.sort(key=lambda x: CATEGORIES.index(x[2]) if x[2] in CATEGORIES else 999)

        if items:
            cols = st.columns(len(items), gap="medium")
            for i, (ic, cl, ct) in enumerate(items):
                with cols[i]:
                    if os.path.exists(cl[1]):
                        st.image(cl[1], caption=f"{ic} {ct}", use_container_width=True)

        kws = [c[4] for _, c, _ in items if c[4]]
        if kws:
            st.caption(f"关键词: {' + '.join(kws)}")
        st.markdown('</div>', unsafe_allow_html=True)
