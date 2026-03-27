import streamlit as st
import os
import uuid
from PIL import Image
import database

# 页面配置
st.set_page_config(page_title="衣服管理助手", page_icon="👔", layout="wide")

# 自定义CSS样式
st.markdown("""
<style>
    /* 主标题样式 */
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2C3E50;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* 卡片样式 */
    .cloth-card {
        background: white;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
        margin-bottom: 20px;
    }
    .cloth-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }

    /* 标签样式 */
    .tag {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 2px;
    }
    .tag-season-spring { background: #FFE5B4; color: #D2691E; }
    .tag-season-summer { background: #B0E0E6; color: #1E90FF; }
    .tag-season-winter { background: #E6E6FA; color: #9370DB; }
    .tag-category-top { background: #FFFACD; color: #DAA520; }
    .tag-category-bottom { background: #E0FFFF; color: #20B2AA; }

    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    [data-testid="stSidebar"] .stRadio > label {
        color: white !important;
        font-weight: bold;
    }

    /* 按钮样式 */
    .stButton > button {
        border-radius: 10px;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 10px 20px;
    }
    .stButton > button:hover {
        transform: scale(1.05);
    }

    /* 上传区域 */
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        background: #f8f9ff;
    }

    /* 结果统计 */
    .result-count {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 1rem;
    }

    /* 搭配预览 */
    .outfit-preview {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 20px;
        padding: 30px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 初始化数据库
database.init_db()

# 上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 侧边栏导航
st.sidebar.markdown("<h2 style='color: white; text-align: center;'>👔 衣服管理</h2>", unsafe_allow_html=True)
page = st.sidebar.radio("", ["上传衣服", "浏览衣服", "搭配"], label_visibility="collapsed")

# ===== 上传页面 =====
if page == "上传衣服":
    st.markdown("<h1 class='main-title'>📤 上传新衣服</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.2], gap="large")

    with col1:
        st.markdown("<div class='upload-area'>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.markdown("<div class='cloth-card'>", unsafe_allow_html=True)
            st.image(image, caption="预览图片", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        if uploaded_file:
            st.markdown("<div class='cloth-card'>", unsafe_allow_html=True)
            with st.form("cloth_form", clear_on_submit=True):
                st.markdown("### 📝 衣服信息")

                col_season, col_category = st.columns(2)
                with col_season:
                    season = st.selectbox("季节", ["春秋装", "夏装", "冬装"], help="选择适合的季节")
                with col_category:
                    category = st.selectbox("类型", ["上装", "下装"], help="选择上装或下装")

                keywords = st.text_input("关键词", placeholder="如：蓝色、休闲、上班、棉麻", help="用逗号分隔多个关键词")

                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                with col_btn2:
                    submit = st.form_submit_button("💾 保存衣服", use_container_width=True)

                if submit:
                    ext = uploaded_file.name.split('.')[-1]
                    filename = f"{uuid.uuid4()}.{ext}"
                    image_path = os.path.join(UPLOAD_DIR, filename)

                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    image.save(image_path)

                    database.add_cloth(image_path, season, category, keywords)
                    st.success("✅ 保存成功！")
            st.markdown("</div>", unsafe_allow_html=True)

# ===== 浏览页面 =====
elif page == "浏览衣服":
    st.markdown("<h1 class='main-title'>👚 我的衣橱</h1>", unsafe_allow_html=True)

    # 筛选区域
    with st.container():
        st.markdown("<div class='cloth-card'>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
        with col1:
            filter_season = st.selectbox("季节", ["全部", "春秋装", "夏装", "冬装"])
        with col2:
            filter_category = st.selectbox("类型", ["全部", "上装", "下装"])
        with col3:
            filter_keyword = st.text_input("🔍 搜索关键词", placeholder="输入关键词...", label_visibility="collapsed")
        with col4:
            st.write("")
            st.write("")
            btn_clear = st.button("🔄 重置")
        st.markdown("</div>", unsafe_allow_html=True)

        if btn_clear:
            st.rerun()

    clothes = database.get_clothes_by_filter(filter_season, filter_category, filter_keyword)

    st.markdown(f"<p class='result-count'>共 {len(clothes)} 件衣服</p>", unsafe_allow_html=True)

    if clothes:
        cols = st.columns(4)
        for i, cloth in enumerate(clothes):
            with cols[i % 4]:
                st.markdown("<div class='cloth-card'>", unsafe_allow_html=True)
                if os.path.exists(cloth[1]):
                    st.image(cloth[1], use_container_width=True)
                else:
                    st.warning("⚠️ 图片不存在")

                # 标签
                season_class = "tag-season-spring" if cloth[2] == "春秋装" else ("tag-season-summer" if cloth[2] == "夏装" else "tag-season-winter")
                category_class = "tag-category-top" if cloth[3] == "上装" else "tag-category-bottom"

                st.markdown(f"""
                <span class='tag {season_class}'>{cloth[2]}</span>
                <span class='tag {category_class}'>{cloth[3]}</span>
                """, unsafe_allow_html=True)

                if cloth[4]:
                    st.markdown(f"<p style='margin-top: 10px;'>🏷️ {cloth[4]}</p>", unsafe_allow_html=True)

                if st.button("🗑️ 删除", key=f"del_{cloth[0]}"):
                    database.delete_cloth(cloth[0])
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='text-align: center; padding: 50px; color: #999;'>
            <h2>📭 还没有衣服</h2>
            <p>去上传页面添加你的第一件衣服吧！</p>
        </div>
        """, unsafe_allow_html=True)

# ===== 搭配页面 =====
elif page == "搭配":
    st.markdown("<h1 class='main-title'>✨ 穿搭搭配</h1>", unsafe_allow_html=True)

    tops = database.get_clothes_by_category("上装")
    bottoms = database.get_clothes_by_category("下装")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("<div class='cloth-card'>", unsafe_allow_html=True)
        st.markdown("### 👕 上装")
        if tops:
            top_options = {f"{c[2]} | {c[4] if c[4] else '无关键词'}": c for c in tops}
            options_list = ["选择上装..."] + list(top_options.keys())
            selected_top = st.selectbox("", options_list, label_visibility="collapsed", key="top_select")
        else:
            st.info("还没有上装，先去上传一些吧！")
            selected_top = None
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='cloth-card'>", unsafe_allow_html=True)
        st.markdown("### 👖 下装")
        if bottoms:
            bottom_options = {f"{c[2]} | {c[4] if c[4] else '无关键词'}": c for c in bottoms}
            options_list = ["选择下装..."] + list(bottom_options.keys())
            selected_bottom = st.selectbox("", options_list, label_visibility="collapsed", key="bottom_select")
        else:
            st.info("还没有下装，先去上传一些吧！")
            selected_bottom = None
        st.markdown("</div>", unsafe_allow_html=True)

    if selected_top and selected_bottom and selected_top != "选择上装..." and selected_bottom != "选择下装...":
        st.markdown("<div class='outfit-preview'>", unsafe_allow_html=True)
        st.markdown("### 🎉 搭配效果", unsafe_allow_html=True)

        top_cloth = top_options[selected_top]
        bottom_cloth = bottom_options[selected_bottom]

        col1, col2 = st.columns(2, gap="large")

        with col1:
            if os.path.exists(top_cloth[1]):
                st.image(top_cloth[1], caption=f"👕 {top_cloth[2]} - {top_cloth[3]}", use_container_width=True)

        with col2:
            if os.path.exists(bottom_cloth[1]):
                st.image(bottom_cloth[1], caption=f"👖 {bottom_cloth[2]} - {bottom_cloth[3]}", use_container_width=True)

        st.markdown("---")
        st.markdown(f"**搭配关键词**: {top_cloth[4] if top_cloth[4] else ''} + {bottom_cloth[4] if bottom_cloth[4] else ''}", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
