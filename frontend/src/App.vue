<template>
  <div class="app">
    <!-- 顶部导航 -->
    <nav class="navbar">
      <div class="logo">👔 衣服管理</div>
      <div class="nav-tabs">
        <button :class="{ active: activeTab === 'upload' }" @click="activeTab = 'upload'">📤 上传</button>
        <button :class="{ active: activeTab === 'browse' }" @click="activeTab = 'browse'">👚 浏览</button>
        <button :class="{ active: activeTab === 'match' }" @click="activeTab = 'match'">✨ 搭配</button>
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

            <label class="checkbox">
              <input type="checkbox" v-model="form.removeBg">
              ✂️ 自动抠图（去除背景）
            </label>

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
              <span class="tag season">{{ cloth.season }}</span>
              <span class="tag category">{{ cloth.category }}</span>
              <p v-if="cloth.keywords" class="keywords">{{ cloth.keywords }}</p>
            </div>
            <button class="delete-btn" @click="deleteCloth(cloth.id)">🗑️</button>
          </div>
        </div>

        <div v-if="filteredClothes.length === 0" class="empty">
          <p>还没有衣服</p>
        </div>
      </div>

      <!-- 搭配页面 -->
      <div v-if="activeTab === 'match'" class="page">
        <h1>✨ 搭配</h1>

        <div class="match-layout">
          <!-- 左侧：衣服列表 -->
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

          <!-- 右侧：搭配画布 -->
          <div class="outfit-panel">
            <div class="outfit-header">
              <h3>🎨 搭配画布</h3>
              <button @click="clearOutfit" class="clear-btn">🗑️ 清空</button>
            </div>

            <div class="size-control">
              <label>图片大小：</label>
              <input type="range" v-model="outfitSize" min="60" max="200">
              <span>{{ outfitSize }}px</span>
            </div>

            <div class="outfit-canvas" ref="canvas">
              <div v-for="(item, index) in outfit" :key="index"
                   class="outfit-item"
                   :style="{ left: item.x + 'px', top: item.y + 'px', width: outfitSize + 'px' }"
                   @mousedown="startDrag($event, index)"
                   @touchstart="startDrag($event, index)">
                <img :src="item.image" @error="handleImageError">
                <span class="item-label">{{ item.category }}</span>
                <button class="remove-item" @click="removeFromOutfit(index)">×</button>
              </div>

              <div v-if="outfit.length === 0" class="canvas-hint">
                点击左侧衣服添加到这里
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'

const API_URL = 'http://localhost:8501'

// 状态
const activeTab = ref('upload')
const clothes = ref([])
const saving = ref(false)

// 上传相关
const fileInput = ref(null)
const previewImage = ref(null)
const form = reactive({
  season: '',
  category: '',
  keywords: '',
  removeBg: false
})

// 浏览筛选
const filter = reactive({
  season: '',
  category: '',
  keyword: ''
})

// 搭配相关
const outfit = ref([])
const outfitSize = ref(100)
const expandedCategories = ref(['上装', '下装'])
const isDragging = ref(false)
const dragIndex = ref(-1)
const dragOffset = reactive({ x: 0, y: 0 })

const categories = [
  { value: '上装', label: '上装', icon: '👕' },
  { value: '下装', label: '下装', icon: '👖' },
  { value: '鞋子', label: '鞋子', icon: '👟' },
  { value: '帽子', label: '帽子', icon: '🧢' },
  { value: '首饰', label: '首饰', icon: '📿' },
  { value: '其他配饰', label: '其他配饰', icon: '🎒' }
]

// 加载衣服列表
const loadClothes = async () => {
  try {
    const res = await axios.get(`${API_URL}/api/clothes`)
    clothes.value = res.data
  } catch (e) {
    console.error('加载失败', e)
  }
}

onMounted(loadClothes)

// 筛选后的衣服
const filteredClothes = computed(() => {
  return clothes.value.filter(c => {
    if (filter.season && c.season !== filter.season) return false
    if (filter.category && c.category !== filter.category) return false
    if (filter.keyword && !c.keywords?.includes(filter.keyword)) return false
    return true
  })
})

// 获取图片URL
const getImageUrl = (path) => {
  if (!path) return ''
  return `${API_URL}/api/image/${encodeURIComponent(path)}`
}

const handleImageError = (e) => {
  e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="50" x="50" text-anchor="middle">📷</text></svg>'
}

// 上传处理
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

    await axios.post(`${API_URL}/api/upload`, formData)
    alert('保存成功！')

    previewImage.value = null
    form.season = ''
    form.category = ''
    form.keywords = ''
    form.removeBg = false
    loadClothes()
  } catch (e) {
    alert('保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}

// 删除衣服
const deleteCloth = async (id) => {
  if (confirm('确定删除？')) {
    await axios.delete(`${API_URL}/api/clothes/${id}`)
    loadClothes()
  }
}

// 搭配相关
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
  outfit.value.push({
    clothId: cloth.id,
    category: cloth.category,
    image: getImageUrl(cloth.image_path),
    x: 20 + (outfit.value.length % 3) * 120,
    y: 20 + Math.floor(outfit.value.length / 3) * 120
  })
}

const removeFromOutfit = (index) => {
  outfit.value.splice(index, 1)
}

const clearOutfit = () => {
  outfit.value = []
}

// 拖拽
const startDrag = (e, index) => {
  e.preventDefault()
  isDragging.value = true
  dragIndex.value = index

  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY

  dragOffset.x = clientX - outfit.value[index].x
  dragOffset.y = clientY - outfit.value[index].y

  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('touchmove', onDrag)
  document.addEventListener('touchend', stopDrag)
}

const onDrag = (e) => {
  if (!isDragging.value) return

  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY

  const canvas = document.querySelector('.outfit-canvas')
  if (!canvas) return

  const rect = canvas.getBoundingClientRect()
  let x = clientX - dragOffset.x - rect.left
  let y = clientY - dragOffset.y - rect.top

  x = Math.max(0, Math.min(x, rect.width - outfitSize.value))
  y = Math.max(0, Math.min(y, rect.height - outfitSize.value))

  outfit.value[dragIndex.value].x = x
  outfit.value[dragIndex.value].y = y
}

const stopDrag = () => {
  isDragging.value = false
  dragIndex.value = -1
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
}

.app {
  min-height: 100vh;
}

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

.logo {
  font-size: 18px;
  font-weight: bold;
}

.nav-tabs {
  display: flex;
}

.nav-tabs button {
  background: transparent;
  border: none;
  color: #aaa;
  padding: 16px 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.nav-tabs button:hover {
  color: white;
}

.nav-tabs button.active {
  color: white;
  background: #333;
}

.main-content {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page h1 {
  font-size: 24px;
  margin-bottom: 20px;
  color: #1a1a1a;
}

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

.upload-placeholder {
  color: #999;
}

.upload-placeholder .icon {
  font-size: 48px;
}

.preview-img {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
}

.form {
  margin-top: 20px;
}

.form-row {
  display: flex;
  gap: 10px;
}

.form select, .form input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.keywords-input {
  width: 100%;
  margin-top: 10px;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 16px 0;
  cursor: pointer;
}

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

.save-btn:hover {
  background: #333;
}

.save-btn:disabled {
  opacity: 0.6;
}

.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.filters select, .filters input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.filters input {
  flex: 1;
}

.count {
  color: #666;
  margin-bottom: 16px;
}

.cloth-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
}

.cloth-card {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.cloth-card img {
  width: 100%;
  aspect-ratio: 3/4;
  object-fit: cover;
}

.cloth-info {
  padding: 8px;
}

.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  margin-right: 4px;
}

.tag.season {
  background: #e8f4f8;
  color: #333;
}

.tag.category {
  background: #f5f5f5;
  color: #666;
}

.keywords {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.delete-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0,0,0,0.5);
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
}

.cloth-card:hover .delete-btn {
  opacity: 1;
}

.empty {
  text-align: center;
  padding: 60px;
  color: #999;
}

.match-layout {
  display: flex;
  gap: 20px;
  height: calc(100vh - 180px);
}

.cloth-list-panel {
  width: 300px;
  background: white;
  border-radius: 12px;
  padding: 16px;
  overflow-y: auto;
}

.cloth-list-panel h3 {
  font-size: 16px;
  margin-bottom: 12px;
}

.category-section {
  margin-bottom: 12px;
}

.category-header {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.category-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 0;
}

.mini-cloth {
  width: 60px;
  height: 60px;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
}

.mini-cloth:hover {
  border-color: #1a1a1a;
}

.mini-cloth img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.outfit-panel {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.outfit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.clear-btn {
  padding: 6px 12px;
  background: #f5f5f5;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.size-control {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.size-control input[type="range"] {
  flex: 1;
}

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
}

.outfit-item img {
  width: 100%;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

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
  line-height: 1;
}

.canvas-hint {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #999;
  font-size: 16px;
}
</style>
