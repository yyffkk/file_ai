<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand-card">
        <div class="brand-logo">KB</div>
        <div>
          <div class="brand-title">资料库</div>
          <div class="brand-subtitle">知识库文件管理与问答</div>
        </div>
      </div>

      <div class="sidebar-section">
        <div class="section-head">
          <h3>我的知识库</h3>
          <span>{{ knowledgeBases.length }} 个</span>
        </div>

        <div class="create-form">
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

        <div class="kb-list">
          <button
            v-for="item in knowledgeBases"
            :key="item.id"
            class="kb-item"
            :class="{ active: selectedKnowledgeBaseId === item.id }"
            @click="selectKnowledgeBase(item.id)"
          >
            <div>
              <strong>{{ item.name }}</strong>
              <small>{{ formatDate(item.created_at) }}</small>
            </div>
            <div class="kb-item-meta">
              <span>{{ item.file_count || 0 }} 文件</span>
              <em>{{ item.build_status || '未构建' }}</em>
            </div>
          </button>
          <div v-if="!knowledgeBases.length" class="empty-block">
            还没有知识库，先在上面新建一个。
          </div>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div>
          <p class="eyebrow">Knowledge Base Center</p>
          <h1>{{ selectedKbName || '资料库' }}</h1>
          <p class="top-desc">
            左边选择知识库，右边查看文件、预览/下载，并对当前知识库内容发起问答。
          </p>
        </div>
        <div class="topbar-actions">
          <button class="ghost-btn" @click="refreshAll">刷新</button>
          <button
            class="ghost-btn"
            :disabled="!selectedKnowledgeBaseId || loading.kbBuild"
            @click="buildKnowledgeBase"
          >
            {{ loading.kbBuild ? '构建中...' : '构建知识库' }}
          </button>
        </div>
      </header>

      <section class="summary-grid">
        <div class="summary-card">
          <span>当前知识库</span>
          <strong>{{ selectedKbName || '未选择' }}</strong>
        </div>
        <div class="summary-card">
          <span>构建状态</span>
          <strong>{{ selectedKbBuildStatus }}</strong>
        </div>
        <div class="summary-card">
          <span>文件数量</span>
          <strong>{{ kbFiles.length }}</strong>
        </div>
      </section>

      <section class="workspace-grid">
        <div class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-tag">Files</p>
              <h2>文件列表</h2>
            </div>
          </div>

          <div class="upload-bar">
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

          <div class="table-wrap">
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
          <div class="panel-header">
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

          <div v-else-if="!previewFileInfo" class="empty-block preview-box">
            选中文件后，可在这里预览。PDF 直接展示，Word 转成网页预览，TXT 显示文本内容。
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

        <div class="panel qa-panel full-span">
          <div class="panel-header">
            <div>
              <p class="panel-tag">Q&A</p>
              <h2>知识库问答</h2>
            </div>
          </div>

          <div class="qa-form">
            <textarea
              v-model="question"
              placeholder="例如：这个资料库里有没有公司资质、案例经验、项目实施方案？"
            />
            <div class="qa-actions">
              <input v-model.number="topK" type="number" min="1" max="10" />
              <button
                class="primary-btn"
                :disabled="!selectedKnowledgeBaseId || !question.trim() || loading.ask"
                @click="askKnowledgeBase"
              >
                {{ loading.ask ? '问答中...' : '开始问答' }}
              </button>
            </div>
          </div>

          <div class="qa-result">
            <div class="answer-card">
              <div class="result-title">回答</div>
              <div class="result-content">{{ qaAnswer.answer || '这里会显示问答结果。' }}</div>
            </div>

            <div class="source-card">
              <div class="result-title">命中文件</div>
              <div v-if="qaAnswer.sources?.length" class="source-list">
                <span v-for="(item, index) in qaAnswer.sources" :key="`${item}-${index}`" class="source-tag">
                  {{ item }}
                </span>
              </div>
              <div v-else class="muted-text">暂无命中文件。</div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import mammoth from 'mammoth/mammoth.browser'
import api from './api'

const newKbName = ref('')
const selectedKnowledgeBaseId = ref('')
const knowledgeBases = ref([])
const kbFiles = ref([])
const documentFile = ref(null)
const previewFileInfo = ref(null)
const previewLoading = ref(false)
const previewHtml = ref('')
const previewText = ref('')
const question = ref('')
const topK = ref(4)
const qaAnswer = ref({ answer: '', sources: [], chunks: [], score: [] })

const loading = ref({
  createKb: false,
  kbList: false,
  kbFiles: false,
  documentUpload: false,
  kbBuild: false,
  ask: false
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
  qaAnswer.value = { answer: '', sources: [], chunks: [], score: [] }
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

  if (file.suffix?.toLowerCase() === '.pdf') {
    return
  }

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

async function askKnowledgeBase() {
  if (!selectedKnowledgeBaseId.value || !question.value.trim()) return
  try {
    loading.value.ask = true
    const { data } = await api.post('/api/kb/ask', {
      knowledge_base_id: selectedKnowledgeBaseId.value,
      question: question.value,
      top_k: topK.value
    })
    qaAnswer.value = data.data || { answer: '', sources: [], chunks: [], score: [] }
  } catch (error) {
    window.alert(getErrorMessage(error))
  } finally {
    loading.value.ask = false
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
