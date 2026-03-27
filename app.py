import streamlit as st
import os
import uuid
from PIL import Image
import database

# 页面配置
st.set_page_config(page_title="衣服管理助手", page_icon="👔", layout="wide")

# 初始化数据库
database.init_db()

# 上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 侧边栏导航
page = st.sidebar.radio("功能", ["上传衣服", "浏览衣服", "搭配"])

# ===== 上传页面 =====
if page == "上传衣服":
    st.title("👔 上传衣服")

    col1, col2 = st.columns([1, 2])

    with col1:
        uploaded_file = st.file_uploader("选择图片", type=["jpg", "jpeg", "png"])

    with col2:
        if uploaded_file:
            # 显示图片
            image = Image.open(uploaded_file)
            st.image(image, caption="预览", use_container_width=True)

            # 表单
            with st.form("cloth_form"):
                season = st.selectbox("季节", ["春秋装", "夏装", "冬装"])
                category = st.selectbox("类型", ["上装", "下装"])
                keywords = st.text_input("关键词", placeholder="如：蓝色、休闲、上班")

                submit = st.form_submit_button("保存")

                if submit:
                    # 保存图片
                    ext = uploaded_file.name.split('.')[-1]
                    filename = f"{uuid.uuid4()}.{ext}"
                    image_path = os.path.join(UPLOAD_DIR, filename)

                    # 转换为RGB并保存
                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    image.save(image_path)

                    # 保存到数据库
                    database.add_cloth(image_path, season, category, keywords)
                    st.success("保存成功！")

# ===== 浏览页面 =====
elif page == "浏览衣服":
    st.title("👕 浏览衣服")

    # 筛选
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_season = st.selectbox("季节", ["全部", "春秋装", "夏装", "冬装"])
    with col2:
        filter_category = st.selectbox("类型", ["全部", "上装", "下装"])
    with col3:
        filter_keyword = st.text_input("搜索关键词", placeholder="输入关键词搜索")

    # 获取筛选后的衣服
    clothes = database.get_clothes_by_filter(filter_season, filter_category, filter_keyword)

    st.divider()
    st.write(f"共 {len(clothes)} 件衣服")

    # 显示
    if clothes:
        cols = st.columns(4)
        for i, cloth in enumerate(clothes):
            with cols[i % 4]:
                if os.path.exists(cloth[1]):
                    st.image(cloth[1], use_container_width=True)
                else:
                    st.warning("图片不存在")
                st.markdown(f"**{cloth[3]}** - {cloth[2]}")
                st.caption(f"关键词: {cloth[4] if cloth[4] else '无'}")
                if st.button("删除", key=f"del_{cloth[0]}"):
                    database.delete_cloth(cloth[0])
                    st.rerun()
    else:
        st.info("没有找到匹配的衣服")

# ===== 搭配页面 =====
elif page == "搭配":
    st.title("👖 搭配")

    # 获取上装和下装
    tops = database.get_clothes_by_category("上装")
    bottoms = database.get_clothes_by_category("下装")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("上装")
        if tops:
            top_options = {f"{c[2]} - {c[4]}": c[0] for c in tops}
            top_options = ["请选择上装"] + list(top_options.keys())
            selected_top = st.selectbox("选择上装", top_options)
        else:
            st.info("暂无上装，请先上传")

    with col2:
        st.subheader("下装")
        if bottoms:
            bottom_options = {f"{c[2]} - {c[4]}": c[0] for c in bottoms}
            bottom_options = ["请选择下装"] + list(bottom_options.keys())
            selected_bottom = st.selectbox("选择下装", bottom_options)
        else:
            st.info("暂无下装，请先上传")

    # 显示搭配结果
    if selected_top != "请选择上装" and selected_bottom != "请选择下装":
        st.divider()
        st.subheader("搭配效果")

        top_cloth = next(c for c in tops if f"{c[2]} - {c[4]}" == selected_top)
        bottom_cloth = next(c for c in bottoms if f"{c[2]} - {c[4]}" == selected_bottom)

        col1, col2 = st.columns(2)
        with col1:
            if os.path.exists(top_cloth[1]):
                st.image(top_cloth[1], caption="上装", use_container_width=True)
        with col2:
            if os.path.exists(bottom_cloth[1]):
                st.image(bottom_cloth[1], caption="下装", use_container_width=True)
