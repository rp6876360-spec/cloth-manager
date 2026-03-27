import streamlit as st
import os
import uuid
from PIL import Image
import database

# 页面配置
st.set_page_config(page_title="衣服管理助手", page_icon="👔", layout="wide")

# Shadcn风格CSS
st.markdown("""
<style>
    /* 全局重置 */
    .stApp {
        background: #FAFAFA;
    }

    /* 主标题 */
    h1 {
        font-size: 1.875rem;
        font-weight: 600;
        letter-spacing: -0.025em;
        color: #171717;
        margin-bottom: 1.5rem;
    }

    /* 卡片样式 */
    .card {
        background: white;
        border: 1px solid #E5E5E5;
        border-radius: 8px;
        padding: 1.5rem;
    }

    /* 按钮样式 */
    .stButton > button {
        background: white;
        border: 1px solid #E5E5E5;
        border-radius: 6px;
        color: #171717;
        font-weight: 500;
        padding: 0.5rem 1rem;
        transition: all 0.15s;
    }
    .stButton > button:hover {
        background: #F5F5F5;
        border-color: #D4D4D4;
    }

    /* Primary按钮 */
    .primary-btn button {
        background: #171717;
        border-color: #171717;
        color: white;
    }
    .primary-btn button:hover {
        background: #404040;
        border-color: #404040;
    }

    /* 输入框 */
    .stTextInput > div > div,
    .stSelectbox > div > div {
        background: white;
        border-color: #E5E5E5;
        border-radius: 6px;
    }

    /* 侧边栏 */
    [data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #E5E5E5;
    }
    [data-testid="stSidebar"] h2 {
        color: #171717;
        font-weight: 600;
    }
    [data-testid="stSidebar"] .stRadio > label {
        color: #525252;
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        transition: all 0.15s;
    }
    [data-testid="stSidebar"] .stRadio > label:hover {
        background: #F5F5F5;
    }
    [data-testid="stSidebar"] .stRadio > div[aria-checked="true"] > label {
        background: #F5F5F5;
        font-weight: 500;
    }

    /* 标签样式 */
    .tag {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        font-size: 0.875rem;
        font-weight: 500;
        border-radius: 9999px;
        border: 1px solid;
    }
    .tag-spring { background: #FEF3C7; border-color: #FCD34D; color: #92400E; }
    .tag-summer { background: #DBEAFE; border-color: #93C5FD; color: #1E40AF; }
    .tag-winter { background: #EDE9FE; border-color: #C4B5FD; color: #5B21B6; }
    .tag-top { background: #FEF3C7; border-color: #FCD34D; color: #92400E; }
    .tag-bottom { background: #CFFAFE; border-color: #67E8F9; color: #155E75; }
    .tag-shoes { background: #FFEDD5; border-color: #FDBA74; color: #9A3412; }
    .tag-hat { background: #F3E8FF; border-color: #D8B4FE; color: #6B21A8; }
    .tag-jewelry { background: #FCE7F3; border-color: #F9A8D4; color: #9D174D; }
    .tag-accessory { background: #D1FAE5; border-color: #6EE7B7; color: #065F46; }

    /* 上传区域 */
    .upload-box {
        border: 2px dashed #D4D4D4;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        background: #FAFAFA;
    }

    /* 图片网格 */
    .image-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
    }

    .image-card {
        background: white;
        border: 1px solid #E5E5E5;
        border-radius: 8px;
        overflow: hidden;
    }
    .image-card img {
        width: 100%;
        aspect-ratio: 3/4;
        object-fit: cover;
    }
    .image-card-content {
        padding: 0.75rem;
    }
    .image-card-title {
        font-weight: 500;
        font-size: 0.875rem;
        color: #171717;
    }
    .image-card-meta {
        font-size: 0.75rem;
        color: #737373;
        margin-top: 0.25rem;
    }

    /* 搭配预览 */
    .outfit-section {
        background: white;
        border: 1px solid #E5E5E5;
        border-radius: 8px;
        padding: 1.5rem;
    }
    .outfit-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 1rem;
        margin-top: 1rem;
    }

    /* 筛选栏 */
    .filter-bar {
        background: white;
        border: 1px solid #E5E5E5;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }

    /* 空状态 */
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: #737373;
    }
    .empty-state h3 {
        font-weight: 500;
        color: #171717;
        margin-bottom: 0.5rem;
    }

    /* 分隔线 */
    hr {
        border: none;
        border-top: 1px solid #E5E5E5;
        margin: 1.5rem 0;
    }

    /* 选中状态 */
    div[aria-checked="true"] {
        background: #F5F5F5 !important;
    }
</style>
""", unsafe_allow_html=True)

# 初始化数据库
database.init_db()

# 上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 配置
CATEGORIES = ["上装", "下装", "鞋子", "帽子", "首饰", "其他配饰"]
CATEGORY_ICONS = {
    "上装": "👕", "下装": "👖", "鞋子": "👟",
    "帽子": "🧢", "首饰": "📿", "其他配饰": "🎒"
}

# 侧边栏
st.sidebar.markdown("## 👔 衣服管理")
page = st.sidebar.radio("导航", ["上传衣服", "浏览衣服", "搭配"], label_visibility="collapsed")

# ===== 上传页面 =====
if page == "上传衣服":
    st.title("上传衣服")

    col1, col2 = st.columns([1, 1], gap="2rem")

    with col1:
        st.markdown('<div class="upload-box">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("选择图片", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.markdown('<div class="card" style="margin-top: 1rem;">', unsafe_allow_html=True)
            st.image(image, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if uploaded_file:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            with st.form("cloth_form", clear_on_submit=True):
                col_season, col_cat = st.columns(2)
                with col_season:
                    season = st.selectbox("季节", ["春秋装", "夏装", "冬装"])
                with col_cat:
                    category = st.selectbox("类型", CATEGORIES)

                keywords = st.text_input("关键词", placeholder="如：蓝色、休闲、上班")

                st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
                submit = st.form_submit_button("保存", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                if submit:
                    ext = uploaded_file.name.split('.')[-1]
                    filename = f"{uuid.uuid4()}.{ext}"
                    image_path = os.path.join(UPLOAD_DIR, filename)

                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    image.save(image_path)

                    database.add_cloth(image_path, season, category, keywords)
                    st.success("保存成功")
            st.markdown('</div>', unsafe_allow_html=True)

# ===== 浏览页面 =====
elif page == "浏览衣服":
    st.title("我的衣橱")

    # 筛选
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
    with col1:
        filter_season = st.selectbox("季节", ["全部", "春秋装", "夏装", "冬装"])
    with col2:
        filter_category = st.selectbox("类型", ["全部"] + CATEGORIES)
    with col3:
        filter_keyword = st.text_input("搜索", placeholder="关键词...", label_visibility="collapsed")
    with col4:
        if st.button("重置"):
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    clothes = database.get_clothes_by_filter(filter_season, filter_category, filter_keyword)

    st.caption(f"共 {len(clothes)} 件")

    if clothes:
        cols = st.columns(4)
        for i, cloth in enumerate(clothes):
            with cols[i % 4]:
                st.markdown('<div class="image-card">', unsafe_allow_html=True)
                if os.path.exists(cloth[1]):
                    st.image(cloth[1], use_container_width=True)
                st.markdown('<div class="image-card-content">', unsafe_allow_html=True)

                # 标签
                season_tag = "spring" if cloth[2] == "春秋装" else ("summer" if cloth[2] == "夏装" else "winter")
                cat_tag = {"上装": "top", "下装": "bottom", "鞋子": "shoes", "帽子": "hat", "首饰": "jewelry", "其他配饰": "accessory"}.get(cloth[3], "top")

                st.markdown(f'<span class="tag tag-{season_tag}">{cloth[2]}</span> <span class="tag tag-{cat_tag}">{cloth[3]}</span>', unsafe_allow_html=True)

                if cloth[4]:
                    st.markdown(f'<p class="image-card-meta">{cloth[4]}</p>', unsafe_allow_html=True)

                if st.button("删除", key=f"del_{cloth[0]}"):
                    database.delete_cloth(cloth[0])
                    st.rerun()
                st.markdown('</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('''
        <div class="empty-state">
            <h3>暂无衣服</h3>
            <p>去上传页面添加衣服吧</p>
        </div>
        ''', unsafe_allow_html=True)

# ===== 搭配页面 =====
elif page == "搭配":
    st.title("搭配")

    # 获取数据
    clothes_by_cat = {cat: database.get_clothes_by_category(cat) for cat in CATEGORIES}

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 选择单品")

    selected = {}

    # 第一行
    c1, c2, c3 = st.columns(3)
    with c1:
        opts = ["不选"] + [f"{c[2]} | {c[4] or '无'}" for c in clothes_by_cat["上装"]] if clothes_by_cat["上装"] else []
        selected["上装"] = st.selectbox("👕 上装", opts) if opts else st.caption("暂无上装")
    with c2:
        opts = ["不选"] + [f"{c[2]} | {c[4] or '无'}" for c in clothes_by_cat["下装"]] if clothes_by_cat["下装"] else []
        selected["下装"] = st.selectbox("👖 下装", opts) if opts else st.caption("暂无下装")
    with c3:
        opts = ["不选"] + [f"{c[2]} | {c[4] or '无'}" for c in clothes_by_cat["鞋子"]] if clothes_by_cat["鞋子"] else []
        selected["鞋子"] = st.selectbox("👟 鞋子", opts) if opts else st.caption("暂无鞋子")

    # 第二行
    c4, c5, c6 = st.columns(3)
    with c4:
        opts = ["不选"] + [f"{c[2]} | {c[4] or '无'}" for c in clothes_by_cat["帽子"]] if clothes_by_cat["帽子"] else []
        selected["帽子"] = st.selectbox("🧢 帽子", opts) if opts else st.caption("暂无帽子")
    with c5:
        opts = ["不选"] + [f"{c[2]} | {c[4] or '无'}" for c in clothes_by_cat["首饰"]] if clothes_by_cat["首饰"] else []
        selected["首饰"] = st.selectbox("📿 首饰", opts) if opts else st.caption("暂无首饰")
    with c6:
        opts = ["不选"] + [f"{c[2]} | {c[4] or '无'}" for c in clothes_by_cat["其他配饰"]] if clothes_by_cat["其他配饰"] else []
        selected["其他配饰"] = st.selectbox("🎒 配饰", opts) if opts else st.caption("暂无配饰")

    st.markdown('</div>', unsafe_allow_html=True)

    # 搭配预览
    has_sel = any(v and v != "不选" for v in selected.values() if v)

    if has_sel:
        st.markdown('<div class="outfit-section">', unsafe_allow_html=True)
        st.markdown("### 搭配效果")

        display_items = []
        for cat, sel in selected.items():
            if sel and sel != "不选":
                for c in clothes_by_cat[cat]:
                    if f"{c[2]} | {c[4] or '无'}" == sel:
                        display_items.append((CATEGORY_ICONS[cat], c, cat))
                        break

        # 按类别顺序排列
        display_items.sort(key=lambda x: CATEGORIES.index(x[2]) if x[2] in CATEGORIES else 999)

        if display_items:
            cols = st.columns(len(display_items))
            for i, (icon, cloth, cat) in enumerate(display_items):
                with cols[i]:
                    if os.path.exists(cloth[1]):
                        st.image(cloth[1], caption=f"{icon} {cat}", use_container_width=True)

        keywords = [c[4] for _, c, _ in display_items if c[4]]
        if keywords:
            st.caption(f"关键词: {' + '.join(keywords)}")

        st.markdown('</div>', unsafe_allow_html=True)
