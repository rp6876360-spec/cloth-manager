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

    # 初始化session state
    if "outfit_items" not in st.session_state:
        st.session_state.outfit_items = []

    # 衣服选择区
    st.markdown("### 📋 选择衣服")

    # 按类别显示
    for cat in CATEGORIES:
        items = clothes_by[cat]
        if items:
            st.markdown(f"**{CATEGORY_ICONS[cat]} {cat}** ({len(items)}件)")
            cols = st.columns(min(len(items), 6))
            for i, c in enumerate(items):
                with cols[i]:
                    if os.path.exists(c[1]):
                        with open(c[1], "rb") as f:
                            b64 = base64.b64encode(f.read()).decode()
                        st.markdown(f'<img src="data:image/png;base64,{b64}" style="width:80px; height:100px; object-fit:contain; border:1px solid #ddd; border-radius:4px;">', unsafe_allow_html=True)
                        if st.button("添加", key=f"add_{c[0]}", use_container_width=True):
                            # 添加到搭配列表
                            item_data = {
                                "id": c[0],
                                "category": cat,
                                "icon": CATEGORY_ICONS[cat],
                                "image": b64,
                                "x": 50 + len(st.session_state.outfit_items) * 80,
                                "y": 50,
                                "size": 100
                            }
                            st.session_state.outfit_items.append(item_data)
                            st.rerun()

    st.markdown("---")

    # 搭配画布
    st.markdown("### 🎨 搭配画布（可拖拽、调整大小）")

    if st.session_state.outfit_items:
        if st.button("🗑️ 清空全部"):
            st.session_state.outfit_items = []
            st.rerun()

        # 生成拖拽界面
        items_html = ""
        for i, item in enumerate(st.session_state.outfit_items):
            items_html += f'''
            <div class="draggable" data-idx="{i}" style="position:absolute; left:{item['x']}px; top:{item['y']}px; width:{item['size']}px; cursor:move;">
                <img src="data:image/png;base64,{item['image']}" style="width:100%; pointer-events:none;">
                <div style="text-align:center; font-size:10px; background:#333; color:white; padding:1px 4px; border-radius:3px;">{item['icon']}</div>
            </div>
            '''

        st.markdown(f"""
        <div id="canvas" style="position:relative; width:100%; height:400px; background:linear-gradient(to bottom, #e8f4f8, #d4e7ed); border-radius:12px; border:2px dashed #aaa; overflow:hidden;">
            <div style="position:absolute; top:8px; left:10px; font-size:12px; color:#666;">💡 拖拽移动衣服位置</div>
            {items_html}
        </div>
        <script>
        (function(){{
            const canvas = document.getElementById('canvas');
            if(!canvas) return;
            let drag = null, offX = 0, offY = 0;

            canvas.addEventListener('mousedown', e => {{
                const el = e.target.closest('.draggable');
                if(el) {{
                    drag = el;
                    const r = el.getBoundingClientRect();
                    offX = e.clientX - r.left;
                    offY = e.clientY - r.top;
                    el.style.zIndex = 999;
                }}
            }});

            document.addEventListener('mousemove', e => {{
                if(drag){{
                    const cr = canvas.getBoundingClientRect();
                    let x = e.clientX - cr.left - offX;
                    let y = e.clientY - cr.top - offY;
                    x = Math.max(0, Math.min(x, cr.width - drag.offsetWidth));
                    y = Math.max(0, Math.min(y, cr.height - drag.offsetHeight));
                    drag.style.left = x + 'px';
                    drag.style.top = y + 'px';
                }}
            }});

            document.addEventListener('mouseup', () => {{
                if(drag) {{ drag.style.zIndex = 1; drag = null; }}
            }});
        }})();
        </script>
        """, unsafe_allow_html=True)

        # 调整大小控制
        st.markdown("### ⚙️ 调整大小")
        cols = st.columns(min(len(st.session_state.outfit_items), 4))

        for i, item in enumerate(st.session_state.outfit_items):
            with cols[i % 4]:
                st.caption(f"{item['icon']} {item['category']}")
                new_size = st.slider(f"大小", 50, 200, item['size'], key=f"size_{i}")
                if new_size != item['size']:
                    st.session_state.outfit_items[i]['size'] = new_size
                    st.rerun()
                if st.button("移除", key=f"remove_{i}"):
                    st.session_state.outfit_items.pop(i)
                    st.rerun()

    else:
        st.info("👆 从上方选择衣服添加到搭配画布")
