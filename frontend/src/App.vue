<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand-card">
        <div class="brand-logo">KB</div>
        <div>
          <div class="brand-title">文件智能助手</div>
          <div class="brand-subtitle">知识库管理 + Agent 助手 + AI 记录</div>
        </div>
      </div>

      <div class="sidebar-section nav-section">
        <div class="section-head">
          <h3>功能导航</h3>
        </div>
        <div class="nav-list">
          <button class="nav-item" :class="{ active: currentPage === 'library' }" @click="currentPage = 'library'">
            <span class="nav-item-icon">📚</span>
            <div>
              <strong>我的知识库</strong>
              <small>管理知识库与文件</small>
            </div>
          </button>
          <button class="nav-item" :class="{ active: currentPage === 'agent' }" @click="currentPage = 'agent'">
            <span class="nav-item-icon">🤖</span>
            <div>
              <strong>Agent 助手</strong>
              <small>智能生成与辅助处理</small>
            </div>
          </button>
          <button class="nav-item" :class="{ active: currentPage === 'record' }" @click="currentPage = 'record'">
            <span class="nav-item-icon">📝</span>
            <div>
              <strong>AI 记录</strong>
              <small>沉淀和保存输出结果</small>
            </div>
          </button>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <template v-if="currentPage === 'library'">
        <section class="library-main-grid layout-kb-compact">
          <div class="panel knowledge-column-panel knowledge-column-panel-dominant">
            <div class="panel-header knowledge-column-header">
              <div>
                <p class="panel-tag">Knowledge Bases</p>
                <h2>我的知识库</h2>
              </div>
              <span class="knowledge-count">共 {{ knowledgeBases.length }} 个</span>
            </div>

            <div class="create-form knowledge-create-form">
              <input
                v-model="newKbName"
                type="text"
                placeholder="输入知识库名称"
                @keyup.enter="createKnowledgeBase"
              />
              <button
                class="primary-btn"
                :disabled="!newKbName.trim() || loading.createKb"
                @click="createKnowledgeBase"
              >
                {{ loading.createKb ? '创建中...' : '新建' }}
              </button>
            </div>

            <div class="knowledge-column-list knowledge-column-list-dominant">
              <button
                v-for="item in knowledgeBases"
                :key="item.id"
                class="knowledge-list-item knowledge-list-item-dominant"
                :class="{ active: selectedKnowledgeBaseId === item.id }"
                @click="selectKnowledgeBase(item.id)"
              >
                <div class="knowledge-list-item-top">
                  <strong>{{ item.name }}</strong>
                </div>
                <div class="knowledge-list-item-bottom">
                  <small>{{ formatDate(item.created_at) }}</small>
                  <em>{{ item.build_status || '未构建' }}</em>
                </div>
              </button>

              <div v-if="!knowledgeBases.length" class="empty-block knowledge-empty-block">
                还没有知识库，先在上面新建一个。
              </div>
            </div>
          </div>

          <div class="library-content-column">
            <header class="library-toolbar inline-library-toolbar">
              <div class="library-toolbar-main">
                <div class="library-toolbar-label">当前知识库</div>
                <div class="library-toolbar-title">{{ selectedKbName || '我的知识库' }}</div>
              </div>
              <div class="library-toolbar-status">
                <span>构建状态</span>
                <strong>{{ selectedKbBuildStatus }}</strong>
              </div>
            </header>

            <div class="panel file-panel">
              <div class="panel-header panel-header-stack-mobile">
                <div>
                  <p class="panel-tag">Files</p>
                  <h2>文件列表</h2>
                </div>
                <button
                  class="ghost-btn"
                  :disabled="!selectedKnowledgeBaseId || loading.kbBuild"
                  @click="buildKnowledgeBase"
                >
                  {{ loading.kbBuild ? '构建中...' : '构建知识库' }}
                </button>
              </div>

              <div class="upload-bar upload-bar-elevated">
                <label class="upload-picker">
                  <input type="file" accept=".pdf,.doc,.docx,.txt" @change="onDocumentFileChange" />
                  <span>{{ documentFile?.name || '选择 PDF / Word / TXT 文件' }}</span>
                </label>
                <button
                  class="primary-btn"
                  :disabled="!selectedKnowledgeBaseId || !documentFile || loading.documentUpload"
                  @click="uploadLibraryDocument"
                >
                  {{ loading.documentUpload ? '上传中...' : '上传到当前知识库' }}
                </button>
              </div>

              <div class="table-wrap table-wrap-modern">
                <table class="file-table">
                  <thead>
                    <tr>
                      <th>文件名</th>
                      <th>类型</th>
                      <th>大小</th>
                      <th>更新时间</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in kbFiles" :key="item.name">
                      <td class="name-cell">{{ item.name }}</td>
                      <td>{{ normalizeSuffix(item.suffix) }}</td>
                      <td>{{ formatFileSize(item.size) }}</td>
                      <td>{{ formatDate(item.updated_at) }}</td>
                      <td>
                        <div class="table-actions">
                          <button class="mini-btn" @click="previewFile(item)">预览</button>
                          <a class="mini-btn link-like" :href="downloadUrl(item)" target="_blank" rel="noreferrer">下载</a>
                        </div>
                      </td>
                    </tr>
                    <tr v-if="!kbFiles.length">
                      <td colspan="5" class="empty-row">当前知识库暂无文件。</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="panel preview-panel">
              <div class="panel-header panel-header-stack-mobile">
                <div>
                  <p class="panel-tag">Preview</p>
                  <h2>文件预览</h2>
                </div>
                <div v-if="previewFileInfo" class="preview-actions">
                  <span class="preview-badge">{{ previewFileInfo.name }}</span>
                  <a class="mini-btn link-like" :href="downloadUrl(previewFileInfo)" target="_blank" rel="noreferrer">下载文件</a>
                </div>
              </div>

              <div v-if="previewLoading" class="empty-block preview-box">预览加载中...</div>

              <div v-else-if="!previewFileInfo" class="empty-block preview-box preview-empty-state">
                <div class="preview-empty-icon">📄</div>
                <div>选中文件后，可在这里预览。PDF 直接展示，Word 转成网页预览，TXT 显示文本内容。</div>
              </div>

              <iframe
                v-else-if="isPdfPreview"
                class="preview-frame"
                :src="previewContentUrl(previewFileInfo)"
                title="pdf-preview"
              />

              <div v-else-if="isWordPreview" class="docx-preview preview-box" v-html="previewHtml"></div>

              <pre v-else class="text-preview preview-box">{{ previewText }}</pre>
            </div>
          </div>
        </section>
      </template>

      <template v-else-if="currentPage === 'agent'">
        <header class="hero-panel">
          <div>
            <p class="eyebrow">Agent Assistant</p>
            <h1>Agent 助手</h1>
            <p class="top-desc">
              承接原“AI 自动写标书”能力，后续可继续接入 Agent 工作流、LangGraph 和自动生成流程。
            </p>
          </div>
          <div class="hero-side hero-side-muted">
            <div class="hero-side-label">当前状态</div>
            <div class="hero-side-value">前端占位中</div>
          </div>
        </header>

        <section class="writer-layout">
          <div class="panel writer-input-panel">
            <div class="panel-header">
              <div>
                <p class="panel-tag">Input</p>
                <h2>用户需求</h2>
              </div>
            </div>
            <textarea
              v-model="writerRequirement"
              class="writer-requirement"
              placeholder="请在这里输入用户需求，例如：
1. 项目背景
2. 招标要求
3. 需要重点体现的能力
4. 交付周期
5. 商务条款等"
            />
            <div class="writer-note">当前仅保留界面，不调用后端生成。</div>
          </div>

          <div class="panel writer-output-panel">
            <div class="panel-header">
              <div>
                <p class="panel-tag">Output</p>
                <h2>助手输出</h2>
              </div>
              <button class="ghost-btn" disabled>后续接 Agent 工作流</button>
            </div>
            <div class="writer-output-box">
              {{ writerOutput || '这里是 Agent 助手的大输出框，后续接入生成能力后，会在这里展示完整结果。' }}
            </div>
          </div>
        </section>
      </template>

      <template v-else>
        <header class="hero-panel">
          <div>
            <p class="eyebrow">AI Record</p>
            <h1>AI 记录</h1>
            <p class="top-desc">
              用于记录和沉淀 Agent 助手输出过的内容，后续可扩展保存、分类、检索与导出能力。
            </p>
          </div>
          <div class="hero-side hero-side-muted">
            <div class="hero-side-label">记录状态</div>
            <div class="hero-side-value">待接存储能力</div>
          </div>
        </header>

        <section class="record-layout">
          <div class="panel record-editor-panel">
            <div class="panel-header">
              <div>
                <p class="panel-tag">Record Input</p>
                <h2>记录内容</h2>
              </div>
            </div>
            <textarea
              v-model="recordContent"
              class="record-textarea"
              placeholder="可将 Agent 助手的输出结果、整理后的重点、备注说明等记录在这里。"
            />
            <div class="writer-note">当前先保留前端占位，后续可接入保存、分类、检索能力。</div>
          </div>

          <div class="panel record-guide-panel">
            <div class="panel-header">
              <div>
                <p class="panel-tag">Record Plan</p>
                <h2>使用场景</h2>
              </div>
            </div>
            <div class="record-guide-list">
              <div class="record-guide-item">
                <strong>记录助手答案</strong>
                <p>把 Agent 助手生成的标书段落、答复建议、分析结果保存下来。</p>
              </div>
              <div class="record-guide-item">
                <strong>沉淀二次编辑稿</strong>
                <p>允许用户在原始 AI 输出基础上做人工修订，形成最终版本记录。</p>
              </div>
              <div class="record-guide-item">
                <strong>后续可扩展</strong>
                <p>可继续增加分类、标签、搜索、关联知识库、导出等能力。</p>
              </div>
            </div>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import mammoth from 'mammoth/mammoth.browser'
import api from './api'

const currentPage = ref('library')
const newKbName = ref('')
const selectedKnowledgeBaseId = ref('')
const knowledgeBases = ref([])
const kbFiles = ref([])
const documentFile = ref(null)
const previewFileInfo = ref(null)
const previewLoading = ref(false)
const previewHtml = ref('')
const previewText = ref('')
const writerRequirement = ref('')
const writerOutput = ref('')
const recordContent = ref('')

const loading = ref({
  createKb: false,
  kbList: false,
  kbFiles: false,
  documentUpload: false,
  kbBuild: false
})

const selectedKbName = computed(() => knowledgeBases.value.find(item => item.id === selectedKnowledgeBaseId.value)?.name || '')
const selectedKbBuildStatus = computed(() => knowledgeBases.value.find(item => item.id === selectedKnowledgeBaseId.value)?.build_status || '未构建')
const isPdfPreview = computed(() => previewFileInfo.value?.suffix?.toLowerCase() === '.pdf')
const isWordPreview = computed(() => previewFileInfo.value?.suffix?.toLowerCase() === '.docx')

onMounted(async () => {
  await refreshAll()
})

async function refreshAll() {
  await fetchKnowledgeBases()
  if (selectedKnowledgeBaseId.value) {
    await fetchKbFiles(selectedKnowledgeBaseId.value)
  }
}

async function fetchKnowledgeBases() {
  try {
    loading.value.kbList = true
    const { data } = await api.get('/api/kb')
    knowledgeBases.value = data.data || []
    if (!selectedKnowledgeBaseId.value && knowledgeBases.value.length) {
      selectedKnowledgeBaseId.value = knowledgeBases.value[0].id
    }
  } finally {
    loading.value.kbList = false
  }
}

async function fetchKbFiles(knowledgeBaseId = selectedKnowledgeBaseId.value) {
  if (!knowledgeBaseId) {
    kbFiles.value = []
    return
  }
  try {
    loading.value.kbFiles = true
    const { data } = await api.get(`/api/kb/${encodeURIComponent(knowledgeBaseId)}/files`)
    kbFiles.value = data.data || []

    if (previewFileInfo.value) {
      const matched = kbFiles.value.find(item => item.name === previewFileInfo.value.name)
      previewFileInfo.value = matched || null
      if (!matched) {
        previewHtml.value = ''
        previewText.value = ''
      }
    }
  } finally {
    loading.value.kbFiles = false
  }
}

async function selectKnowledgeBase(id) {
  selectedKnowledgeBaseId.value = id
  previewFileInfo.value = null
  previewHtml.value = ''
  previewText.value = ''
  currentPage.value = 'library'
  await fetchKbFiles(id)
}

async function createKnowledgeBase() {
  try {
    loading.value.createKb = true
    const { data } = await api.post('/api/kb', { name: newKbName.value })
    newKbName.value = ''
    await fetchKnowledgeBases()
    if (data.data?.id) {
      await selectKnowledgeBase(data.data.id)
    }
  } catch (error) {
    window.alert(getErrorMessage(error))
  } finally {
    loading.value.createKb = false
  }
}

function onDocumentFileChange(event) {
  documentFile.value = event.target.files?.[0] || null
}

async function uploadLibraryDocument() {
  if (!selectedKnowledgeBaseId.value || !documentFile.value) return
  try {
    loading.value.documentUpload = true
    const formData = new FormData()
    formData.append('file', documentFile.value)
    await api.post(`/api/kb/${encodeURIComponent(selectedKnowledgeBaseId.value)}/upload`, formData)
    documentFile.value = null
    await fetchKnowledgeBases()
    await fetchKbFiles(selectedKnowledgeBaseId.value)
  } catch (error) {
    window.alert(getErrorMessage(error))
  } finally {
    loading.value.documentUpload = false
  }
}

async function buildKnowledgeBase() {
  if (!selectedKnowledgeBaseId.value) return
  try {
    loading.value.kbBuild = true
    await api.post('/api/kb/build', {
      knowledge_base_id: selectedKnowledgeBaseId.value,
      file_names: null
    })
    await fetchKnowledgeBases()
    await fetchKbFiles(selectedKnowledgeBaseId.value)
  } catch (error) {
    window.alert(getErrorMessage(error))
  } finally {
    loading.value.kbBuild = false
  }
}

async function previewFile(file) {
  previewFileInfo.value = file
  previewHtml.value = ''
  previewText.value = ''

  if (file.suffix?.toLowerCase() === '.pdf') return

  try {
    previewLoading.value = true

    if (file.suffix?.toLowerCase() === '.docx') {
      const response = await api.get(previewContentUrl(file), { responseType: 'arraybuffer' })
      const { value } = await mammoth.convertToHtml({ arrayBuffer: response.data })
      previewHtml.value = value || '<p>该 Word 文件暂无可展示内容。</p>'
      return
    }

    if (file.suffix?.toLowerCase() === '.doc') {
      previewText.value = '旧版 .doc 文件暂不支持网页内预览，请直接下载查看。'
      return
    }

    const response = await api.get(previewTextUrl(file), { responseType: 'text' })
    previewText.value = typeof response.data === 'string' ? response.data : '无法读取文本内容'
  } catch (error) {
    previewText.value = getErrorMessage(error)
  } finally {
    previewLoading.value = false
  }
}

function previewTextUrl(file) {
  return `/api/kb/${encodeURIComponent(selectedKnowledgeBaseId.value)}/files/${encodeURIComponent(file.name)}/preview`
}

function previewContentUrl(file) {
  return `/api/kb/${encodeURIComponent(selectedKnowledgeBaseId.value)}/files/${encodeURIComponent(file.name)}/content`
}

function downloadUrl(file) {
  return `${api.defaults.baseURL}/api/kb/${encodeURIComponent(selectedKnowledgeBaseId.value)}/files/${encodeURIComponent(file.name)}/download`
}

function formatFileSize(size) {
  if (size == null) return '-'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(2)} MB`
}

function formatDate(value) {
  if (!value) return '-'
  return value.replace('T', ' ').slice(0, 19)
}

function normalizeSuffix(value) {
  return String(value || '').replace('.', '').toUpperCase() || '-'
}

function getErrorMessage(error) {
  return error?.response?.data?.detail || error?.message || '请求失败'
}
</script>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(body) {
  margin: 0;
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: linear-gradient(180deg, #f5f8ff 0%, #eef3fb 100%);
  color: #1b2b4b;
}

:global(#app) {
  min-height: 100vh;
}

.app-shell {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  min-height: 100vh;
  gap: 24px;
  padding: 24px;
}

.sidebar,
.main-content {
  min-width: 0;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.brand-card,
.sidebar-section,
.panel,
.library-toolbar {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(131, 156, 214, 0.18);
  border-radius: 28px;
  box-shadow: 0 20px 50px rgba(84, 116, 180, 0.12);
}

.brand-card {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 28px;
}

.brand-logo {
  width: 78px;
  height: 78px;
  border-radius: 24px;
  background: linear-gradient(180deg, #1f3363 0%, #263f77 100%);
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 28px;
  font-weight: 800;
}

.brand-title {
  font-size: 28px;
  font-weight: 800;
  line-height: 1.2;
}

.brand-subtitle {
  margin-top: 8px;
  font-size: 15px;
  line-height: 1.6;
  color: #637ba8;
}

.sidebar-section {
  padding: 26px;
}

.section-head h3 {
  margin: 0 0 20px;
  font-size: 18px;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 18px 20px;
  border-radius: 24px;
  border: 1px solid transparent;
  background: #f9fbff;
  color: #1b2b4b;
  text-align: left;
  cursor: pointer;
}

.nav-item.active {
  background: linear-gradient(180deg, #edf3ff 0%, #e6eeff 100%);
  border-color: #a9c0ff;
}

.nav-item-icon {
  width: 44px;
  height: 44px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: #e6edff;
  font-size: 22px;
}

.nav-item strong {
  display: block;
  font-size: 18px;
  line-height: 1.3;
}

.nav-item small {
  display: block;
  margin-top: 6px;
  font-size: 14px;
  color: #6980a8;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.library-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 20px 28px;
}

.inline-library-toolbar {
  margin-bottom: 0;
}

.layout-kb-compact {
  grid-template-columns: 340px minmax(0, 1fr);
}

.layout-kb-compact .knowledge-column-panel {
  min-height: calc(100vh - 48px);
}

.layout-kb-compact .knowledge-column-list {
  gap: 10px;
}

.layout-kb-compact .knowledge-list-item {
  padding: 14px 16px;
}

.layout-kb-compact .knowledge-list-item-top strong {
  font-size: 16px;
}

.layout-kb-compact .knowledge-list-item-bottom {
  margin-top: 12px;
}

.layout-kb-compact .panel-header h2 {
  font-size: 22px;
}

.layout-kb-compact .create-form input {
  font-size: 15px;
}

.layout-kb-compact .primary-btn {
  padding: 12px 18px;
}

.layout-kb-compact .library-content-column {
  gap: 16px;
}

.layout-kb-compact .library-toolbar-title {
  font-size: 24px;
}

.layout-kb-compact .library-toolbar-status {
  padding: 12px 16px;
}

.layout-kb-compact .library-toolbar-status strong {
  font-size: 16px;
}

.library-toolbar-label,
.panel-tag,
.eyebrow {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #3c62d6;
}

.library-toolbar-title {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 800;
  line-height: 1.2;
}

.library-toolbar-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-radius: 18px;
  background: linear-gradient(180deg, #eef4ff 0%, #e8f0ff 100%);
  color: #59709a;
  white-space: nowrap;
}

.library-toolbar-status span {
  font-size: 14px;
}

.library-toolbar-status strong {
  font-size: 18px;
  color: #1f3363;
}

.library-main-grid {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.library-content-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.panel {
  padding: 24px;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.panel-header h2 {
  margin: 8px 0 0;
  font-size: 26px;
  line-height: 1.2;
}

.knowledge-column-header {
  align-items: center;
}

.knowledge-count {
  font-size: 14px;
  color: #6f84ab;
}

.create-form {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.create-form input,
.upload-picker,
.writer-requirement,
.record-textarea,
.mini-btn,
.primary-btn,
.ghost-btn {
  font: inherit;
}

.create-form input,
.upload-picker,
.writer-requirement,
.record-textarea {
  width: 100%;
  border: 1px solid #d7e1f6;
  border-radius: 20px;
  background: #fff;
  color: #1b2b4b;
}

.create-form input {
  padding: 14px 18px;
  font-size: 16px;
}

.primary-btn,
.ghost-btn,
.mini-btn {
  border: none;
  border-radius: 18px;
  padding: 14px 22px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
}

.primary-btn {
  background: linear-gradient(180deg, #7fa0f3 0%, #6d8fe8 100%);
  color: #fff;
}

.ghost-btn,
.mini-btn {
  background: #edf3ff;
  color: #1f3363;
}

.primary-btn:disabled,
.ghost-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.knowledge-column-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.knowledge-list-item {
  width: 100%;
  padding: 14px 16px;
  border-radius: 20px;
  border: 1px solid #d5e2ff;
  background: #f7faff;
  text-align: left;
  cursor: pointer;
  color: #1b2b4b;
}

.knowledge-list-item.active {
  border-color: #8eafff;
  box-shadow: 0 14px 30px rgba(84, 116, 180, 0.14);
}

.knowledge-list-item-top,
.knowledge-list-item-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.knowledge-list-item-top strong {
  font-size: 18px;
  line-height: 1.3;
}

.knowledge-list-item-bottom {
  margin-top: 18px;
  color: #6b80a6;
  font-size: 13px;
}

.knowledge-list-item-bottom em {
  font-style: normal;
  font-weight: 700;
  color: #3159d3;
}

.kb-file-badge,
.preview-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: #e6edff;
  color: #59709a;
  font-size: 13px;
  font-weight: 700;
}

.upload-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 22px;
}

.upload-picker {
  position: relative;
  display: flex;
  align-items: center;
  min-height: 72px;
  padding: 0 22px;
  overflow: hidden;
  font-size: 16px;
  color: #6f84ab;
}

.upload-picker input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid #e1e9f8;
  border-radius: 22px;
  background: #fff;
}

.file-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 15px;
}

.file-table th,
.file-table td {
  padding: 18px 20px;
  border-bottom: 1px solid #edf1f8;
  text-align: left;
}

.file-table th {
  color: #667ca3;
  font-size: 14px;
  font-weight: 700;
}

.file-table tbody tr:last-child td {
  border-bottom: none;
}

.name-cell {
  max-width: 320px;
  word-break: break-all;
}

.table-actions,
.preview-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.preview-box {
  min-height: 360px;
  border: 1px solid #e1e9f8;
  border-radius: 22px;
  background: #fdfefe;
  padding: 20px;
}

.preview-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 14px;
  color: #6f84ab;
  text-align: center;
  font-size: 15px;
}

.preview-empty-icon {
  font-size: 40px;
}

.preview-frame {
  width: 100%;
  min-height: 720px;
  border: 1px solid #e1e9f8;
  border-radius: 22px;
  background: #fff;
}

.docx-preview {
  line-height: 1.75;
}

.text-preview {
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: 14px;
}

.empty-block,
.empty-row,
.writer-note {
  color: #6f84ab;
  font-size: 14px;
}

.writer-layout,
.record-layout {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.writer-requirement,
.record-textarea,
.writer-output-box {
  min-height: 360px;
  padding: 18px;
  font-size: 15px;
  line-height: 1.7;
}

.writer-output-box,
.record-guide-list {
  border: 1px solid #e1e9f8;
  border-radius: 22px;
  background: #fff;
}

.record-guide-list {
  padding: 6px;
}

.record-guide-item {
  padding: 18px;
  border-radius: 18px;
}

.record-guide-item + .record-guide-item {
  margin-top: 10px;
}

.top-desc,
.hero-panel,
.summary-grid,
.summary-card {
  display: none;
}

@media (max-width: 1200px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .library-main-grid,
  .writer-layout,
  .record-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .app-shell {
    padding: 16px;
    gap: 16px;
  }

  .brand-card,
  .sidebar-section,
  .panel,
  .library-toolbar {
    border-radius: 22px;
  }

  .library-toolbar,
  .panel-header,
  .upload-bar,
  .create-form {
    flex-direction: column;
    align-items: stretch;
  }

  .library-toolbar-title {
    font-size: 24px;
  }

  .brand-title {
    font-size: 24px;
  }

  .panel-header h2 {
    font-size: 22px;
  }
}
</style>
