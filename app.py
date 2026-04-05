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

    uploaded = st.file_uploader("选择图片", type=["jpg", "jpeg", "png"])

    if uploaded:
        st.write(f"已选择: {uploaded.name}")

        with st.form("form"):
            s = st.selectbox("季节", ["春秋装", "夏装", "冬装"])
            cat = st.selectbox("类型", CATEGORIES)
            kw = st.text_input("关键词", placeholder="蓝色、休闲")
            remove_bg = st.checkbox("✂️ 自动抠图（去除背景）", value=False)

            if st.form_submit_button("💾 保存"):
                with st.spinner("处理中..."):
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
                            pil_img = remove(pil_img)
                            img = np.array(pil_img)
                        except Exception as e:
                            st.warning(f"抠图失败: {e}")

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
                    with open(c[1], "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    st.markdown(f'<img src="data:image/png;base64,{b64}" style="width:100%;">', unsafe_allow_html=True)
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

    # 准备所有衣服数据
    all_clothes = []
    for cat in CATEGORIES:
        for c in clothes_by[cat]:
            if os.path.exists(c[1]):
                with open(c[1], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                all_clothes.append({
                    "id": c[0],
                    "category": cat,
                    "icon": CATEGORY_ICONS[cat],
                    "keywords": c[4] or "-",
                    "image": b64
                })

    if not all_clothes:
        st.info("还没有衣服，去上传页面添加吧")
    else:
        st.markdown("### 📋 衣服列表（点击添加到搭配区）")

        # 显示衣服列表
        cols = st.columns(6, gap="small")
        for i, item in enumerate(all_clothes):
            with cols[i % 6]:
                st.markdown(f"""
                <div style="text-align:center; cursor:pointer; padding:5px; border:1px solid #ddd; border-radius:8px; margin-bottom:10px; background:white;">
                    <img src="data:image/png;base64,{item['image']}" style="width:100%; max-height:80px; object-fit:contain;">
                    <div style="font-size:12px;">{item['icon']} {item['category']}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"添加", key=f"add_{item['id']}"):
                    if "outfit" not in st.session_state:
                        st.session_state.outfit = []
                    st.session_state.outfit.append(item)
                    st.rerun()

        # 搭配区域
        st.markdown("---")
        st.markdown("### 🎨 搭配区域")

        if "outfit" in st.session_state and st.session_state.outfit:
            # 清空按钮
            if st.button("🗑️ 清空搭配"):
                st.session_state.outfit = []
                st.rerun()

            # 生成拖拽界面HTML
            items_html = ""
            for i, item in enumerate(st.session_state.outfit):
                items_html += f'''
                <div class="draggable-item" data-index="{i}" style="position:absolute; left:{50 + i * 120}px; top:50px; width:100px; cursor:move; user-select:none;">
                    <img src="data:image/png;base64,{item['image']}" style="width:100%; pointer-events:none;">
                    <div style="text-align:center; font-size:11px; background:rgba(0,0,0,0.6); color:white; padding:2px; border-radius:4px;">{item['icon']}</div>
                </div>
                '''

            st.markdown(f"""
            <div id="canvas-container" style="position:relative; width:100%; height:400px; background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius:12px; overflow:hidden;">
                <div style="position:absolute; top:10px; left:10px; color:white; font-size:12px; opacity:0.7;">💡 拖拽衣服调整位置</div>
                {items_html}
            </div>

            <script>
            (function() {{
                const container = document.getElementById('canvas-container');
                if (!container) return;

                let draggedItem = null;
                let offsetX = 0;
                let offsetY = 0;

                container.addEventListener('mousedown', function(e) {{
                    const item = e.target.closest('.draggable-item');
                    if (item) {{
                        draggedItem = item;
                        const rect = item.getBoundingClientRect();
                        offsetX = e.clientX - rect.left;
                        offsetY = e.clientY - rect.top;
                        item.style.zIndex = 1000;
                    }}
                }});

                document.addEventListener('mousemove', function(e) {{
                    if (draggedItem) {{
                        const containerRect = container.getBoundingClientRect();
                        let newX = e.clientX - containerRect.left - offsetX;
                        let newY = e.clientY - containerRect.top - offsetY;

                        // 限制在容器内
                        newX = Math.max(0, Math.min(newX, containerRect.width - 100));
                        newY = Math.max(0, Math.min(newY, containerRect.height - 120));

                        draggedItem.style.left = newX + 'px';
                        draggedItem.style.top = newY + 'px';
                    }}
                }});

                document.addEventListener('mouseup', function(e) {{
                    if (draggedItem) {{
                        draggedItem.style.zIndex = 1;
                        draggedItem = null;
                    }}
                }});
            }})();
            </script>
            """, unsafe_allow_html=True)

            # 显示已添加的衣服（可移除）
            st.markdown("**已添加的衣服:**")
            cols = st.columns(len(st.session_state.outfit))
            for i, item in enumerate(st.session_state.outfit):
                with cols[i]:
                    st.caption(f"{item['icon']} {item['category']}")
                    if st.button("移除", key=f"remove_{i}"):
                        st.session_state.outfit.pop(i)
                        st.rerun()

        else:
            st.info("点击上方衣服的「添加」按钮开始搭配")
