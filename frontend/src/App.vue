<template>
  <div class="app">
    <!-- 顶部导航 -->
    <nav class="navbar">
      <div class="logo">👔 衣服管理</div>
      <div class="nav-tabs">
        <button :class="{ active: activeTab === 'upload' }" @click="activeTab = 'upload'">📤 上传</button>
        <button :class="{ active: activeTab === 'browse' }" @click="activeTab = 'browse'">👚 浏览</button>
        <button :class="{ active: activeTab === 'match' }" @click="activeTab = 'match'">✨ 搭配</button>
        <button :class="{ active: activeTab === 'stats' }" @click="activeTab = 'stats'; loadStats()">📊 统计</button>
        <button :class="{ active: activeTab === 'outfits' }" @click="activeTab = 'outfits'; loadOutfits()">📚 搭配库</button>
      </div>
    </nav>

    <main class="main-content">
      <!-- 上传页面 -->
      <div v-if="activeTab === 'upload'" class="page">
        <h1>📤 上传衣服</h1>
        <div class="upload-card">
          <div class="upload-area" @click="triggerUpload" @dragover.prevent @drop.prevent="handleDrop">
            <input type="file" ref="fileInput" @change="handleFileSelect" accept="image/*" hidden>
            <div v-if="!previewImage" class="upload-placeholder">
              <span class="icon">📁</span>
              <p>点击或拖拽图片到这里</p>
            </div>
            <img v-else :src="previewImage" class="preview-img">
          </div>
          <div v-if="previewImage" class="form">
            <div class="form-row">
              <select v-model="form.season">
                <option value="">选择季节</option>
                <option value="春秋装">春秋装</option>
                <option value="夏装">夏装</option>
                <option value="冬装">冬装</option>
              </select>
              <select v-model="form.category">
                <option value="">选择类型</option>
                <option value="上装">👕 上装</option>
                <option value="下装">👖 下装</option>
                <option value="鞋子">👟 鞋子</option>
                <option value="帽子">🧢 帽子</option>
                <option value="首饰">📿 首饰</option>
                <option value="其他配饰">🎒 其他配饰</option>
              </select>
            </div>
            <input v-model="form.keywords" placeholder="关键词，如：蓝色、休闲" class="keywords-input">

            <div class="form-row">
              <input v-model="form.brand" placeholder="品牌（选填）" class="half-input">
              <input v-model="form.price" placeholder="价格（选填）" type="number" class="half-input">
            </div>

            <label class="checkbox">
              <input type="checkbox" v-model="form.removeBg">
              ✂️ 自动抠图（去除背景并裁切空白）
            </label>

            <div v-if="detectedInfo" class="detected-info">
              <p>🔍 自动识别：</p>
              <span class="auto-tag">颜色：{{ detectedInfo.color }}</span>
              <span class="auto-tag">风格：{{ detectedInfo.style }}</span>
            </div>

            <button class="save-btn" @click="saveCloth" :disabled="saving">
              {{ saving ? '处理中...' : '💾 保存' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 浏览页面 -->
      <div v-if="activeTab === 'browse'" class="page">
        <h1>👚 我的衣橱</h1>
        <div class="filters">
          <select v-model="filter.season">
            <option value="">全部季节</option>
            <option value="春秋装">春秋装</option>
            <option value="夏装">夏装</option>
            <option value="冬装">冬装</option>
          </select>
          <select v-model="filter.category">
            <option value="">全部类型</option>
            <option value="上装">上装</option>
            <option value="下装">下装</option>
            <option value="鞋子">鞋子</option>
            <option value="帽子">帽子</option>
            <option value="首饰">首饰</option>
            <option value="其他配饰">其他配饰</option>
          </select>
          <input v-model="filter.keyword" placeholder="搜索关键词...">
        </div>
        <p class="count">共 {{ filteredClothes.length }} 件</p>
        <div class="cloth-grid">
          <div v-for="cloth in filteredClothes" :key="cloth.id" class="cloth-card">
            <img :src="getImageUrl(cloth.image_path)" @error="handleImageError">
            <div class="cloth-info">
              <div class="tags-row">
                <span class="tag season">{{ cloth.season }}</span>
                <span class="tag category">{{ cloth.category }}</span>
              </div>
              <div v-if="cloth.color || cloth.style" class="tags-row">
                <span v-if="cloth.color" class="tag color">{{ cloth.color }}</span>
                <span v-if="cloth.style" class="tag style">{{ cloth.style }}</span>
              </div>
              <p v-if="cloth.keywords" class="keywords">{{ cloth.keywords }}</p>
              <p v-if="cloth.brand || cloth.price" class="brand-price">
                <span v-if="cloth.brand">{{ cloth.brand }}</span>
                <span v-if="cloth.price" class="price">¥{{ cloth.price }}</span>
              </p>
            </div>
            <button class="delete-btn" @click="deleteCloth(cloth.id)">🗑️</button>
          </div>
        </div>
        <div v-if="filteredClothes.length === 0" class="empty">
          <p>还没有衣服</p>
        </div>
      </div>

      <!-- 统计页面 -->
      <div v-if="activeTab === 'stats'" class="page">
        <h1>📊 衣柜统计</h1>

        <div class="stats-summary">
          <div class="stat-card">
            <div class="stat-num">{{ stats.total_count }}</div>
            <div class="stat-label">总数量</div>
          </div>
          <div class="stat-card">
            <div class="stat-num">¥{{ stats.total_price || 0 }}</div>
            <div class="stat-label">总价值</div>
          </div>
        </div>

        <div class="stats-grid">
          <div class="chart-card">
            <h3>📂 类型分布</h3>
            <div class="bar-chart">
              <div v-for="(count, cat) in stats.category" :key="cat" class="bar-row">
                <span class="bar-label">{{ cat }}</span>
                <div class="bar-wrap">
                  <div class="bar" :style="{ width: getBarWidth(count, stats.total_count) }"></div>
                  <span class="bar-num">{{ count }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="chart-card">
            <h3>🎨 颜色分布</h3>
            <div class="color-grid">
              <div v-for="(count, color) in stats.color" :key="color" class="color-item">
                <span class="color-dot" :class="getColorClass(color)"></span>
                <span>{{ color }}</span>
                <span class="color-count">{{ count }}</span>
              </div>
            </div>
          </div>

          <div class="chart-card">
            <h3>👔 风格分布</h3>
            <div class="style-list">
              <div v-for="(count, style) in stats.style" :key="style" class="style-item">
                <span>{{ style }}</span>
                <span class="style-count">{{ count }}件</span>
              </div>
            </div>
          </div>

          <div class="chart-card suggestions-card">
            <h3>💡 购物建议</h3>
            <ul class="suggestions-list">
              <li v-for="(s, i) in stats.suggestions" :key="i">{{ s }}</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 搭配页面 -->
      <div v-if="activeTab === 'match'" class="page">
        <h1>✨ 搭配</h1>
        <div class="match-layout">
          <div class="cloth-list-panel">
            <h3>📋 选择衣服</h3>
            <div v-for="cat in categories" :key="cat.value" class="category-section">
              <div class="category-header" @click="toggleCategory(cat.value)">
                <span>{{ cat.icon }} {{ cat.label }}</span>
                <span class="count">({{ getClothesByCategory(cat.value).length }})</span>
              </div>
              <div v-if="expandedCategories.includes(cat.value)" class="category-items">
                <div v-for="cloth in getClothesByCategory(cat.value)" :key="cloth.id"
                     class="mini-cloth" @click="addToOutfit(cloth)">
                  <img :src="getImageUrl(cloth.image_path)" @error="handleImageError">
                </div>
              </div>
            </div>
          </div>

          <div class="outfit-panel">
            <div class="outfit-header">
              <h3>🎨 搭配画布</h3>
              <div class="header-btns">
                <button @click="showSaveDialog = true" class="save-outfit-btn" :disabled="outfit.length === 0">💾 保存</button>
                <button @click="clearOutfit" class="clear-btn">🗑️ 清空</button>
              </div>
            </div>

            <div v-if="selectedItemIndex >= 0 && outfit[selectedItemIndex]" class="item-controls">
              <div class="control-row">
                <label>大小: {{ outfit[selectedItemIndex].size }}px</label>
                <input type="range" v-model="outfit[selectedItemIndex].size" min="50" max="200">
              </div>
              <div class="control-row">
                <label>旋转: {{ outfit[selectedItemIndex].rotation }}°</label>
                <input type="range" v-model="outfit[selectedItemIndex].rotation" min="-180" max="180">
              </div>
            </div>

            <div class="outfit-canvas" ref="canvasRef" @click.self="selectedItemIndex = -1">
              <div v-for="(item, index) in outfit" :key="'item-' + item.clothId + '-' + index"
                   class="outfit-item"
                   :class="{ selected: selectedItemIndex === index }"
                   :style="{
                     left: item.x + 'px',
                     top: item.y + 'px',
                     width: item.size + 'px',
                     zIndex: item.zIndex || 1,
                     transform: 'rotate(' + item.rotation + 'deg)'
                   }"
                   @mousedown.stop="startDrag($event, index)"
                   @touchstart.stop="startDrag($event, index)"
                   @click.stop="selectItem(index)">
                <img :src="item.image" @error="handleImageError" draggable="false">
                <span class="item-label">{{ item.category }}</span>
                <button class="remove-item" @click.stop="removeFromOutfit(index)">×</button>
              </div>
              <div v-if="outfit.length === 0" class="canvas-hint">
                点击左侧衣服添加到这里<br>点击图片可调整大小和旋转
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 搭配库页面 -->
      <div v-if="activeTab === 'outfits'" class="page">
        <h1>📚 搭配库</h1>
        <p class="count">共 {{ savedOutfits.length }} 个搭配</p>
        <div class="outfits-grid">
          <div v-for="outfit in savedOutfits" :key="outfit.id" class="outfit-card">
            <div class="outfit-preview">
              <img v-for="(item, idx) in parseItems(outfit.items).slice(0, 3)" :key="idx"
                   :src="item.image" class="preview-item">
            </div>
            <div class="outfit-info">
              <h4>{{ outfit.name }}</h4>
              <p>{{ parseItems(outfit.items).length }} 件</p>
            </div>
            <div class="outfit-actions">
              <button @click="loadOutfit(outfit)">加载</button>
              <button @click="deleteOutfit(outfit.id)" class="delete">删除</button>
            </div>
          </div>
        </div>
        <div v-if="savedOutfits.length === 0" class="empty">
          <p>还没有保存的搭配</p>
        </div>
      </div>
    </main>

    <!-- 保存搭配弹窗 -->
    <div v-if="showSaveDialog" class="modal-overlay" @click.self="showSaveDialog = false">
      <div class="modal">
        <h3>保存搭配</h3>
        <input v-model="outfitName" placeholder="输入搭配名称" class="modal-input">
        <div class="modal-btns">
          <button @click="showSaveDialog = false">取消</button>
          <button @click="saveOutfit" class="primary">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'

const API_URL = 'http://localhost:5000'

const activeTab = ref('upload')
const clothes = ref([])
const saving = ref(false)
const showSaveDialog = ref(false)
const outfitName = ref('')
const detectedInfo = ref(null)

const fileInput = ref(null)
const previewImage = ref(null)
const form = reactive({
  season: '',
  category: '',
  keywords: '',
  removeBg: false,
  brand: '',
  price: ''
})

const filter = reactive({
  season: '',
  category: '',
  keyword: ''
})

const outfit = ref([])
const selectedItemIndex = ref(-1)
const expandedCategories = ref(['上装', '下装'])
const isDragging = ref(false)
const dragIndex = ref(-1)
const dragOffset = reactive({ x: 0, y: 0 })

const savedOutfits = ref([])
const stats = ref({ category: {}, color: {}, style: {}, season: {}, total_count: 0, total_price: 0, suggestions: [] })

const categories = [
  { value: '上装', label: '上装', icon: '👕' },
  { value: '下装', label: '下装', icon: '👖' },
  { value: '鞋子', label: '鞋子', icon: '👟' },
  { value: '帽子', label: '帽子', icon: '🧢' },
  { value: '首饰', label: '首饰', icon: '📿' },
  { value: '其他配饰', label: '其他配饰', icon: '🎒' }
]

const loadClothes = async () => {
  try {
    const res = await axios.get(`${API_URL}/api/clothes`)
    clothes.value = res.data
  } catch (e) {
    console.error('加载失败', e)
  }
}

const loadOutfits = async () => {
  try {
    const res = await axios.get(`${API_URL}/api/outfits`)
    savedOutfits.value = res.data
  } catch (e) {
    console.error('加载搭配库失败', e)
  }
}

const loadStats = async () => {
  try {
    const res = await axios.get(`${API_URL}/api/statistics`)
    stats.value = res.data
  } catch (e) {
    console.error('加载统计失败', e)
  }
}

onMounted(loadClothes)

const filteredClothes = computed(() => {
  return clothes.value.filter(c => {
    if (filter.season && c.season !== filter.season) return false
    if (filter.category && c.category !== filter.category) return false
    if (filter.keyword && !c.keywords?.includes(filter.keyword)) return false
    return true
  })
})

const getImageUrl = (path) => {
  if (!path) return ''
  return `${API_URL}/api/image/${encodeURIComponent(path)}`
}

const handleImageError = (e) => {
  e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="50" x="50" text-anchor="middle">📷</text></svg>'
}

const triggerUpload = () => fileInput.value?.click()

const handleFileSelect = (e) => {
  const file = e.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => previewImage.value = e.target.result
    reader.readAsDataURL(file)
  }
}

const handleDrop = (e) => {
  const file = e.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    const reader = new FileReader()
    reader.onload = (e) => previewImage.value = e.target.result
    reader.readAsDataURL(file)
  }
}

const saveCloth = async () => {
  if (!form.season || !form.category) {
    alert('请选择季节和类型')
    return
  }
  saving.value = true
  try {
    const file = fileInput.value?.files[0]
    const formData = new FormData()
    formData.append('file', file)
    formData.append('season', form.season)
    formData.append('category', form.category)
    formData.append('keywords', form.keywords)
    formData.append('remove_bg', form.removeBg)
    formData.append('brand', form.brand)
    formData.append('price', form.price)

    const res = await axios.post(`${API_URL}/api/upload`, formData)
    detectedInfo.value = { color: res.data.color, style: res.data.style }
    alert('保存成功！')

    previewImage.value = null
    form.season = ''
    form.category = ''
    form.keywords = ''
    form.removeBg = false
    form.brand = ''
    form.price = ''
    loadClothes()
  } catch (e) {
    alert('保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}

const deleteCloth = async (id) => {
  if (confirm('确定删除？')) {
    await axios.delete(`${API_URL}/api/clothes/${id}`)
    loadClothes()
  }
}

const getClothesByCategory = (cat) => {
  return clothes.value.filter(c => c.category === cat)
}

const toggleCategory = (cat) => {
  const idx = expandedCategories.value.indexOf(cat)
  if (idx >= 0) {
    expandedCategories.value.splice(idx, 1)
  } else {
    expandedCategories.value.push(cat)
  }
}

const addToOutfit = (cloth) => {
  const canvas = document.querySelector('.outfit-canvas')
  let startX = 20, startY = 20
  if (canvas) {
    startX = Math.random() * (canvas.offsetWidth - 150) + 20
    startY = Math.random() * (canvas.offsetHeight - 150) + 20
  }
  outfit.value.push({
    clothId: cloth.id,
    category: cloth.category,
    image: getImageUrl(cloth.image_path),
    x: startX,
    y: startY,
    size: 100,
    rotation: 0,
    zIndex: 1
  })
}

const selectItem = (index) => {
  selectedItemIndex.value = index
}

const removeFromOutfit = (index) => {
  outfit.value.splice(index, 1)
  if (selectedItemIndex.value === index) selectedItemIndex.value = -1
}

const clearOutfit = () => {
  outfit.value = []
  selectedItemIndex.value = -1
}

const canvasRef = ref(null)

const startDrag = (e, index) => {
  e.preventDefault()
  e.stopPropagation()
  isDragging.value = true
  dragIndex.value = index
  selectedItemIndex.value = index

  const canvas = document.querySelector('.outfit-canvas')
  const rect = canvas.getBoundingClientRect()
  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY

  dragOffset.x = clientX - rect.left - outfit.value[index].x
  dragOffset.y = clientY - rect.top - outfit.value[index].y
  outfit.value[index].zIndex = 100

  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('touchmove', onDrag, { passive: false })
  document.addEventListener('touchend', stopDrag)
}

const onDrag = (e) => {
  if (!isDragging.value || dragIndex.value < 0) return
  e.preventDefault()

  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY
  const canvas = document.querySelector('.outfit-canvas')
  if (!canvas) return

  const rect = canvas.getBoundingClientRect()
  const item = outfit.value[dragIndex.value]

  let x = clientX - rect.left - dragOffset.x
  let y = clientY - rect.top - dragOffset.y
  x = Math.max(0, Math.min(x, rect.width - item.size))
  y = Math.max(0, Math.min(y, rect.height - item.size - 20))

  item.x = x
  item.y = y
}

const stopDrag = () => {
  if (dragIndex.value >= 0 && outfit.value[dragIndex.value]) {
    outfit.value[dragIndex.value].zIndex = 1
  }
  isDragging.value = false
  dragIndex.value = -1
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
}

const saveOutfit = async () => {
  if (!outfitName.value.trim()) {
    alert('请输入搭配名称')
    return
  }
  try {
    await axios.post(`${API_URL}/api/outfits`, { name: outfitName.value, items: outfit.value })
    alert('保存成功！')
    showSaveDialog.value = false
    outfitName.value = ''
  } catch (e) {
    alert('保存失败: ' + e.message)
  }
}

const loadOutfit = (saved) => {
  outfit.value = parseItems(saved.items)
  activeTab.value = 'match'
}

const deleteOutfit = async (id) => {
  if (confirm('确定删除？')) {
    await axios.delete(`${API_URL}/api/outfits/${id}`)
    loadOutfits()
  }
}

const parseItems = (itemsStr) => {
  try { return JSON.parse(itemsStr) || [] } catch { return [] }
}

const getBarWidth = (count, total) => {
  if (!total) return '0%'
  return Math.max(10, (count / total) * 100) + '%'
}

const getColorClass = (color) => {
  const map = {
    '白色': 'white', '黑色': 'black', '红色': 'red', '绿色': 'green',
    '蓝色': 'blue', '黄色': 'yellow', '紫色': 'purple', '粉色': 'pink',
    '橙色': 'orange', '棕色': 'brown', '灰色': 'gray'
  }
  return map[color] || 'default'
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
.app { min-height: 100vh; }

.navbar {
  background: #1a1a1a;
  color: white;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
}
.logo { font-size: 18px; font-weight: bold; }
.nav-tabs { display: flex; }
.nav-tabs button {
  background: transparent;
  border: none;
  color: #aaa;
  padding: 16px 14px;
  cursor: pointer;
  font-size: 13px;
}
.nav-tabs button:hover { color: white; }
.nav-tabs button.active { color: white; background: #333; }

.main-content { padding: 20px; max-width: 1400px; margin: 0 auto; }
.page h1 { font-size: 24px; margin-bottom: 20px; color: #1a1a1a; }

.upload-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  max-width: 500px;
  margin: 0 auto;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.upload-placeholder { color: #999; }
.upload-placeholder .icon { font-size: 48px; }
.preview-img { max-width: 100%; max-height: 300px; border-radius: 8px; }

.form { margin-top: 20px; }
.form-row { display: flex; gap: 10px; margin-bottom: 10px; }
.form select, .form input, .keywords-input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}
.keywords-input { width: 100%; margin-top: 0; }
.half-input { flex: 1; }

.checkbox { display: flex; align-items: center; gap: 8px; margin: 16px 0; cursor: pointer; }
.save-btn {
  width: 100%;
  padding: 12px;
  background: #1a1a1a;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
}
.save-btn:hover { background: #333; }
.save-btn:disabled { opacity: 0.6; }

.detected-info {
  background: #f0f9ff;
  border-radius: 8px;
  padding: 12px;
  margin: 12px 0;
}
.detected-info p { font-size: 13px; color: #666; margin-bottom: 8px; }
.auto-tag {
  display: inline-block;
  background: #1a1a1a;
  color: white;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 8px;
}

.filters { display: flex; gap: 10px; margin-bottom: 20px; }
.filters select, .filters input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}
.filters input { flex: 1; }
.count { color: #666; margin-bottom: 16px; }

.cloth-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}
.cloth-card {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.cloth-card img { width: 100%; aspect-ratio: 3/4; object-fit: cover; }
.cloth-info { padding: 10px; }
.tags-row { margin-bottom: 4px; }
.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  margin-right: 4px;
}
.tag.season { background: #e8f4f8; color: #333; }
.tag.category { background: #f5f5f5; color: #666; }
.tag.color { background: #fff3cd; color: #856404; }
.tag.style { background: #d4edda; color: #155724; }
.keywords { font-size: 12px; color: #666; margin-top: 4px; }
.brand-price {
  font-size: 11px;
  color: #888;
  margin-top: 4px;
  display: flex;
  justify-content: space-between;
}
.price { color: #e74c3c; font-weight: bold; }
.delete-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0,0,0,0.5);
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  cursor: pointer;
  opacity: 0;
}
.cloth-card:hover .delete-btn { opacity: 1; }
.empty { text-align: center; padding: 60px; color: #999; }

/* 统计页面 */
.stats-summary { display: flex; gap: 20px; margin-bottom: 24px; }
.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  flex: 1;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.stat-num { font-size: 32px; font-weight: bold; color: #1a1a1a; }
.stat-label { color: #666; margin-top: 4px; }

.stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
.chart-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.chart-card h3 { font-size: 16px; margin-bottom: 16px; }

.bar-chart { }
.bar-row { display: flex; align-items: center; margin-bottom: 8px; }
.bar-label { width: 80px; font-size: 13px; }
.bar-wrap { flex: 1; display: flex; align-items: center; }
.bar {
  height: 20px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
  min-width: 20px;
}
.bar-num { margin-left: 8px; font-size: 12px; color: #666; }

.color-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.color-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.color-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1px solid #ddd;
}
.color-dot.white { background: white; }
.color-dot.black { background: #1a1a1a; }
.color-dot.red { background: #e74c3c; }
.color-dot.green { background: #27ae60; }
.color-dot.blue { background: #3498db; }
.color-dot.yellow { background: #f1c40f; }
.color-dot.purple { background: #9b59b6; }
.color-dot.pink { background: #e91e63; }
.color-dot.orange { background: #e67e22; }
.color-dot.brown { background: #8d6e63; }
.color-dot.gray { background: #9e9e9e; }
.color-dot.default { background: #ccc; }
.color-count { margin-left: auto; color: #666; }

.style-list { }
.style-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
  font-size: 14px;
}
.style-count { color: #666; }

.suggestions-card { }
.suggestions-list { list-style: none; }
.suggestions-list li {
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
  margin-bottom: 8px;
  font-size: 14px;
}

/* 搭配页面 */
.match-layout { display: flex; gap: 20px; height: calc(100vh - 180px); }
.cloth-list-panel {
  width: 220px;
  background: white;
  border-radius: 12px;
  padding: 16px;
  overflow-y: auto;
}
.cloth-list-panel h3 { font-size: 15px; margin-bottom: 12px; }
.category-section { margin-bottom: 10px; }
.category-header {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.category-items { display: flex; flex-wrap: wrap; gap: 6px; padding: 8px 0; }
.mini-cloth {
  width: 45px;
  height: 45px;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
}
.mini-cloth:hover { border-color: #1a1a1a; }
.mini-cloth img { width: 100%; height: 100%; object-fit: cover; }

.outfit-panel {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
}
.outfit-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.header-btns { display: flex; gap: 8px; }
.save-outfit-btn {
  padding: 6px 12px;
  background: #1a1a1a;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.save-outfit-btn:disabled { opacity: 0.5; }
.clear-btn {
  padding: 6px 12px;
  background: #f5f5f5;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.item-controls {
  display: flex;
  gap: 20px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
  margin-bottom: 12px;
}
.control-row { display: flex; align-items: center; gap: 10px; flex: 1; }
.control-row label { font-size: 13px; min-width: 100px; }
.control-row input[type="range"] { flex: 1; }

.outfit-canvas {
  flex: 1;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 12px;
  position: relative;
  overflow: hidden;
}
.outfit-item {
  position: absolute;
  cursor: move;
  user-select: none;
  transition: box-shadow 0.2s;
}
.outfit-item.selected { box-shadow: 0 0 0 3px #1a1a1a; border-radius: 8px; }
.outfit-item img { width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
.item-label {
  display: block;
  text-align: center;
  font-size: 11px;
  background: rgba(0,0,0,0.6);
  color: white;
  padding: 2px;
  border-radius: 0 0 8px 8px;
  margin-top: -4px;
}
.remove-item {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  background: #ff4444;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 16px;
}
.canvas-hint {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #999;
  font-size: 16px;
  text-align: center;
}

/* 搭配库 */
.outfits-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}
.outfit-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.outfit-preview {
  display: flex;
  gap: 4px;
  padding: 8px;
  background: #f5f5f5;
  height: 100px;
}
.preview-item { flex: 1; object-fit: cover; border-radius: 6px; }
.outfit-info { padding: 12px; }
.outfit-info h4 { font-size: 14px; margin-bottom: 4px; }
.outfit-info p { font-size: 12px; color: #666; }
.outfit-actions { display: flex; border-top: 1px solid #eee; }
.outfit-actions button {
  flex: 1;
  padding: 10px;
  border: none;
  background: white;
  cursor: pointer;
  font-size: 13px;
}
.outfit-actions button:first-child { border-right: 1px solid #eee; }
.outfit-actions button.delete { color: #ff4444; }

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: white;
  border-radius: 12px;
  padding: 24px;
  width: 300px;
}
.modal h3 { margin-bottom: 16px; }
.modal-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  margin-bottom: 16px;
}
.modal-btns { display: flex; gap: 10px; }
.modal-btns button { flex: 1; padding: 10px; border: none; border-radius: 6px; cursor: pointer; }
.modal-btns button.primary { background: #1a1a1a; color: white; }
</style>
