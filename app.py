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
    .tag-category-shoes { background: #FFDAB9; color: #CD853F; }
    .tag-category-hat { background: #E6E6FA; color: #8A2BE2; }
    .tag-category-jewelry { background: #FFC0CB; color: #DB7093; }
    .tag-category-accessory { background: #98FB98; color: #228B22; }

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

    /* 多选框样式 */
    .category-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 初始化数据库
database.init_db()

# 上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 服装类别配置
CATEGORIES = ["上装", "下装", "鞋子", "帽子", "首饰", "其他配饰"]
CATEGORY_ICONS = {
    "上装": "👕",
    "下装": "👖",
    "鞋子": "👟",
    "帽子": "🧢",
    "首饰": "📿",
    "其他配饰": "🎒"
}

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
                    category = st.selectbox("类型", CATEGORIES, help="选择服装类型")

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
            filter_category = st.selectbox("类型", ["全部"] + CATEGORIES)
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

                # 根据类别选择样式
                category_class_map = {
                    "上装": "tag-category-top",
                    "下装": "tag-category-bottom",
                    "鞋子": "tag-category-shoes",
                    "帽子": "tag-category-hat",
                    "首饰": "tag-category-jewelry",
                    "其他配饰": "tag-category-accessory"
                }
                category_class = category_class_map.get(cloth[3], "tag-category-top")

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

    # 获取所有类别的衣服
    clothes_by_category = {}
    for cat in CATEGORIES:
        clothes_by_category[cat] = database.get_clothes_by_category(cat)

    # 显示各类别的选择器
    st.markdown("<div class='cloth-card'>", unsafe_allow_html=True)
    st.markdown("### 👔 选择要搭配的单品")

    # 创建多列布局，每行显示可叠穿的类别
    selected_items = {}

    # 第一行：主要衣物（上装、下装、鞋子）
    col1, col2, col3 = st.columns(3)
    with col1:
        if clothes_by_category["上装"]:
            options = ["不选"] + [f"{c[2]} | {c[4] if c[4] else '无'}" for c in clothes_by_category["上装"]]
            selected_items["上装"] = st.selectbox(f"👕 上装", options, key="top_select")
        else:
            st.info("暂无上装")

    with col2:
        if clothes_by_category["下装"]:
            options = ["不选"] + [f"{c[2]} | {c[4] if c[4] else '无'}" for c in clothes_by_category["下装"]]
            selected_items["下装"] = st.selectbox(f"👖 下装", options, key="bottom_select")
        else:
            st.info("暂无下装")

    with col3:
        if clothes_by_category["鞋子"]:
            options = ["不选"] + [f"{c[2]} | {c[4] if c[4] else '无'}" for c in clothes_by_category["鞋子"]]
            selected_items["鞋子"] = st.selectbox(f"👟 鞋子", options, key="shoes_select")
        else:
            st.info("暂无鞋子")

    # 第二行：配饰
    col4, col5, col6 = st.columns(3)
    with col4:
        if clothes_by_category["帽子"]:
            options = ["不选"] + [f"{c[2]} | {c[4] if c[4] else '无'}" for c in clothes_by_category["帽子"]]
            selected_items["帽子"] = st.selectbox(f"🧢 帽子", options, key="hat_select")
        else:
            st.info("暂无帽子")

    with col5:
        if clothes_by_category["首饰"]:
            options = ["不选"] + [f"{c[2]} | {c[4] if c[4] else '无'}" for c in clothes_by_category["首饰"]]
            selected_items["首饰"] = st.selectbox(f"📿 首饰", options, key="jewelry_select")
        else:
            st.info("暂无首饰")

    with col6:
        if clothes_by_category["其他配饰"]:
            options = ["不选"] + [f"{c[2]} | {c[4] if c[4] else '无'}" for c in clothes_by_category["其他配饰"]]
            selected_items["其他配饰"] = st.selectbox(f"🎒 其他配饰", options, key="accessory_select")
        else:
            st.info("暂无配饰")

    st.markdown("</div>", unsafe_allow_html=True)

    # 显示搭配效果
    has_selection = any(v != "不选" for v in selected_items.values() if v)

    if has_selection:
        st.markdown("<div class='outfit-preview'>", unsafe_allow_html=True)
        st.markdown("### 🎉 搭配效果", unsafe_allow_html=True)

        # 准备显示的图片
        display_items = []

        for category, selection in selected_items.items():
            if selection and selection != "不选":
                # 找到对应的衣服
                for c in clothes_by_category[category]:
                    display_str = f"{c[2]} | {c[4] if c[4] else '无'}"
                    if display_str == selection:
                        display_items.append((CATEGORY_ICONS.get(category, "👔"), c, category))
                        break

        # 按顺序显示：上装 -> 下装 -> 鞋子 -> 帽子 -> 首饰 -> 配饰
        display_items.sort(key=lambda x: CATEGORIES.index(x[2]) if x[2] in CATEGORIES else 999)

        # 显示所有选中的单品
        if display_items:
            # 计算需要的列数
            n_items = len(display_items)
            cols = st.columns(min(n_items, 4))

            for i, (icon, cloth, cat) in enumerate(display_items):
                with cols[i % 4]:
                    if os.path.exists(cloth[1]):
                        st.image(cloth[1], caption=f"{icon} {cat}", use_container_width=True)

        # 显示搭配关键词
        keywords_list = [c[4] for _, c, _ in display_items if c[4]]
        if keywords_list:
            st.markdown("---")
            st.markdown(f"**搭配关键词**: {' + '.join(keywords_list)}", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
