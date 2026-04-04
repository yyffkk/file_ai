<template>
  <div class="app-frame">
    <aside class="sidebar">
      <div class="brand-block">
        <div class="brand-logo">AI</div>
        <div>
          <div class="brand-name">TenderOS</div>
          <div class="brand-subtitle">标书智能工作台</div>
        </div>
      </div>

      <nav class="nav-menu">
        <button
          v-for="item in navItems"
          :key="item.key"
          class="nav-item"
          :class="{ active: currentPage === item.key }"
          @click="goPage(item.key)"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-copy">
            <strong>{{ item.label }}</strong>
            <small>{{ item.desc }}</small>
          </span>
        </button>
      </nav>

      <div class="sidebar-summary">
        <div class="summary-item">
          <span>状态</span>
          <strong>{{ currentStatusText }}</strong>
        </div>
        <div class="summary-item">
          <span>当前知识库</span>
          <strong>{{ selectedKbName || '未选择' }}</strong>
        </div>
      </div>
    </aside>

    <div class="main-shell">
      <header class="topbar">
        <div>
          <div class="breadcrumb">工作台 / {{ currentPageLabel }}</div>
          <h1>{{ currentPageMeta.title }}</h1>
          <p>{{ currentPageMeta.desc }}</p>
        </div>
        <div class="topbar-actions compact-actions">
          <button class="tool-btn" @click="toggleTips">{{ showTips ? '隐藏说明' : '查看说明' }}</button>
          <button class="tool-btn secondary" @click="goPage('kb')">知识库</button>
          <button class="tool-btn secondary" @click="goPage('qa')">问答</button>
          <button class="tool-btn secondary" @click="goPage('tender')">标书解析</button>
        </div>
      </header>

      <section v-if="showTips" class="tips-banner">
        <div class="tips-title">使用说明</div>
        <div class="tips-text">{{ currentPageMeta.tips }}</div>
      </section>

      <main class="content-area">
        <section v-if="currentPage === 'kb'" class="page-grid kb-layout">
          <div class="panel left-stack">
            <div class="panel-header">
              <div>
                <div class="section-tag">Knowledge Base</div>
                <h2>知识库列表</h2>
              </div>
              <span class="panel-pill">{{ knowledgeBases.length }} 个</span>
            </div>

            <div class="field">
              <label class="label">新建知识库</label>
              <div class="inline-form">
                <input v-model="newKbName" type="text" placeholder="例如：产品资料库 / 招标模板库 / 制度文件库" />
                <button class="primary-btn" :disabled="!newKbName.trim() || loading.createKb" @click="createKnowledgeBase">
                  {{ loading.createKb ? '创建中...' : '新建' }}
                </button>
              </div>
            </div>

            <div v-if="knowledgeBases.length" class="kb-list">
              <button
                v-for="item in knowledgeBases"
                :key="item.id"
                class="kb-card"
                :class="{ active: selectedKnowledgeBaseId === item.id }"
                @click="selectKnowledgeBase(item.id)"
              >
                <div>
                  <strong>{{ item.name }}</strong>
                  <small>内部ID：{{ item.id }}</small>
                </div>
                <span>{{ item.file_count || 0 }} 个文件</span>
              </button>
            </div>
            <div v-else class="empty-state light-empty short-empty">还没有知识库，先新建一个。</div>
          </div>

          <div class="panel right-stack">
            <div class="panel-header">
              <div>
                <div class="section-tag">Files</div>
                <h2>知识库文件管理</h2>
              </div>
              <span class="panel-pill subtle">{{ selectedKbName || '未选择' }}</span>
            </div>

            <template v-if="selectedKnowledgeBaseId">
              <div class="kb-meta-strip">
                <div><span>显示名</span><strong>{{ selectedKbName }}</strong></div>
                <div><span>内部ID</span><strong>{{ selectedKnowledgeBaseId }}</strong></div>
              </div>

              <label class="upload-area compact-upload">
                <input type="file" @change="onKbFileChange" />
                <div class="upload-title small">{{ kbFileName || '点击选择文件上传到当前知识库' }}</div>
                <div class="upload-desc">支持 PDF / DOCX / TXT</div>
              </label>

              <div class="action-row">
                <button class="primary-btn" :disabled="!kbFile || loading.kbUpload" @click="uploadKbFile">
                  {{ loading.kbUpload ? '上传中...' : '上传文件' }}
                </button>
                <button class="secondary-btn" :disabled="loading.kbBuild" @click="buildKnowledgeBase">
                  {{ loading.kbBuild ? '构建中...' : '构建当前知识库' }}
                </button>
                <button class="secondary-btn" :disabled="loading.migrate" @click="migrateLegacyKnowledgeBases">
                  {{ loading.migrate ? '迁移中...' : '迁移旧知识库' }}
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
                      <td>{{ item.name }}</td>
                      <td>{{ item.suffix }}</td>
                      <td>{{ formatFileSize(item.size) }}</td>
                      <td>{{ formatDate(item.updated_at) }}</td>
                      <td>
                        <div class="table-actions">
                          <button class="link-btn" @click="previewFile(item)">预览</button>
                          <a class="link-btn" :href="downloadUrl(item.name)" target="_blank">下载</a>
                        </div>
                      </td>
                    </tr>
                    <tr v-if="!kbFiles.length">
                      <td colspan="5" class="empty-row">当前知识库还没有文件</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>

            <div v-else class="empty-state light-empty short-empty">请先在左侧选择一个知识库。</div>
          </div>

          <div class="panel preview-panel full-span">
            <div class="panel-header">
              <div>
                <div class="section-tag">Preview</div>
                <h2>在线预览</h2>
              </div>
              <span class="panel-pill subtle">{{ previewFileName || '暂无预览' }}</span>
            </div>

            <div class="preview-toolbar" v-if="previewFileName">
              <span class="preview-badge">{{ previewTypeLabel }}</span>
              <a class="link-btn" :href="downloadUrl(previewFileName)" target="_blank">下载原文件</a>
            </div>

            <div v-if="loading.kbPreview" class="empty-state light-empty large-box">预览加载中...</div>
            <iframe v-else-if="previewMode === 'pdf' && previewUrl" :src="previewUrl" class="preview-frame"></iframe>
            <div v-else-if="previewMode === 'docx'" class="docx-preview result-box light large-box" v-html="previewHtml || 'DOCX 预览为空'"></div>
            <pre v-else-if="previewMode === 'text'" class="result-box light large-box">{{ previewText || '暂无文本内容' }}</pre>
            <div v-else class="empty-state light-empty large-box">点击上方“预览”即可查看文件内容。</div>
          </div>

          <div class="panel result-panel full-span">
            <div class="panel-header">
              <div>
                <div class="section-tag">Result</div>
                <h2>执行结果</h2>
              </div>
              <span class="panel-pill subtle">JSON</span>
            </div>
            <pre class="result-box light">{{ kbActionResult }}</pre>
          </div>
        </section>

        <section v-else-if="currentPage === 'qa'" class="page-grid qa-clean-layout">
          <div class="panel large-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Question</div>
                <h2>知识库问答</h2>
              </div>
              <span class="panel-pill">问答</span>
            </div>

            <div class="field">
              <label class="label">选择知识库</label>
              <select v-model="selectedKnowledgeBaseId" class="select-input">
                <option value="">请选择知识库</option>
                <option v-for="item in knowledgeBases" :key="item.id" :value="item.id">{{ item.name }}</option>
              </select>
            </div>

            <div class="field">
              <label class="label">问题内容</label>
              <textarea v-model="question" placeholder="请输入你的问题，例如：招标文件对交付周期、验收标准、售后服务有什么要求？"></textarea>
            </div>

            <div class="compact-form-row">
              <div class="field no-margin">
                <label class="label">Top K</label>
                <input v-model.number="topK" type="number" min="1" max="10" />
              </div>
              <div class="info-card grow">
                <span>命中文档来源</span>
                <strong>{{ qaResult.sources?.length || 0 }} 个</strong>
              </div>
            </div>

            <div class="action-row">
              <button class="primary-btn" :disabled="!question || !selectedKnowledgeBaseId || loading.ask" @click="askQuestion">
                {{ loading.ask ? '提问中...' : '开始问答' }}
              </button>
            </div>
          </div>

          <div class="panel result-panel clean-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Answer</div>
                <h2>回答结果</h2>
              </div>
              <span class="panel-pill subtle">输出</span>
            </div>

            <div class="answer-box light">{{ qaResult.answer || '暂无结果' }}</div>

            <div class="source-section" v-if="qaResult.sources?.length">
              <div class="sub-title">来源文件</div>
              <div class="tag-list">
                <span class="tag" v-for="(item, index) in qaResult.sources" :key="index">{{ item }}</span>
              </div>
            </div>
          </div>

          <div class="panel full-span clean-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Evidence</div>
                <h2>命中文本片段</h2>
              </div>
              <span class="panel-pill subtle">{{ qaResult.chunks?.length || 0 }} 段</span>
            </div>

            <div v-if="qaResult.chunks?.length" class="chunk-list spacious-chunks">
              <article class="chunk-card light-card" v-for="(chunk, index) in qaResult.chunks" :key="index">
                <div class="chunk-card-top">
                  <span>片段 {{ index + 1 }}</span>
                  <strong>Score {{ qaResult.score?.[index] ?? '-' }}</strong>
                </div>
                <p>{{ chunk }}</p>
              </article>
            </div>
            <div v-else class="empty-state light-empty">暂无命中文本片段</div>
          </div>
        </section>

        <section v-else class="page-grid two-col-soft">
          <div class="panel large-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Tender Upload</div>
                <h2>上传标书文件</h2>
              </div>
              <span class="panel-pill">解析</span>
            </div>

            <label class="upload-area tall light-upload">
              <input type="file" @change="onTenderFileChange" />
              <div class="upload-title">{{ tenderFileName || '点击选择标书文件' }}</div>
              <div class="upload-desc">上传后执行结构化解析</div>
            </label>

            <div class="info-card">
              <span>当前文件</span>
              <strong>{{ tenderFileName || '未选择文件' }}</strong>
            </div>

            <div class="action-row">
              <button class="primary-btn" :disabled="!tenderFile || loading.tender" @click="parseTender">
                {{ loading.tender ? '解析中...' : '上传并解析' }}
              </button>
            </div>
          </div>

          <div class="panel result-panel clean-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Result</div>
                <h2>解析结果</h2>
              </div>
              <span class="panel-pill subtle">JSON</span>
            </div>

            <pre class="result-box light tall-result">{{ tenderResultText }}</pre>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import mammoth from 'mammoth'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import api from './api'

const navItems = [
  { key: 'kb', label: '知识库管理', desc: '新建、上传、预览、下载', icon: '📚' },
  { key: 'qa', label: '知识库问答', desc: 'RAG 问答', icon: '💬' },
  { key: 'tender', label: '标书解析', desc: '结构化解析', icon: '🧾' }
]

const pageMetaMap = {
  kb: {
    title: '知识库管理中心',
    desc: '支持显示名和内部ID分离，并提供更接近真实文件的在线预览。',
    tips: 'PDF 会直接在线展示；DOCX 会在前端解析后在线渲染；TXT 会按文本方式展示。知识库的显示名给人看，内部ID给系统用。'
  },
  qa: {
    title: '知识库问答中心',
    desc: '按知识库维度发起问答，避免不同资料混在一起。',
    tips: '先选择已完成构建的知识库，再提问。回答结果会附带来源文件和命中文本片段。'
  },
  tender: {
    title: '标书解析中心',
    desc: '上传标书后直接查看结构化结果。',
    tips: '优先上传格式清晰的正式文档，解析结果更稳定。'
  }
}

const kbFile = ref(null)
const tenderFile = ref(null)
const question = ref('')
const topK = ref(4)
const kbActionResult = ref('暂无结果')
const qaResult = ref({ answer: '', sources: [], chunks: [], score: [] })
const tenderResult = ref(null)
const currentPage = ref('kb')
const showTips = ref(false)
const newKbName = ref('')
const knowledgeBases = ref([])
const selectedKnowledgeBaseId = ref('')
const kbFiles = ref([])
const previewFileName = ref('')
const previewMode = ref('')
const previewUrl = ref('')
const previewHtml = ref('')
const previewText = ref('')

const loading = reactive({
  createKb: false,
  kbUpload: false,
  kbBuild: false,
  kbFiles: false,
  kbList: false,
  kbPreview: false,
  migrate: false,
  ask: false,
  tender: false
})

const kbFileName = computed(() => kbFile.value?.name || '')
const tenderFileName = computed(() => tenderFile.value?.name || '')
const currentPageMeta = computed(() => pageMetaMap[currentPage.value] || pageMetaMap.kb)
const currentPageLabel = computed(() => navItems.find(item => item.key === currentPage.value)?.label || '知识库管理')
const selectedKbName = computed(() => knowledgeBases.value.find(item => item.id === selectedKnowledgeBaseId.value)?.name || '')
const currentStatusText = computed(() => {
  if (Object.values(loading).some(Boolean)) return '处理中'
  return '空闲'
})
const tenderResultText = computed(() => {
  if (!tenderResult.value) return '暂无结果'
  return JSON.stringify(tenderResult.value, null, 2)
})
const previewTypeLabel = computed(() => {
  if (previewMode.value === 'pdf') return 'PDF 在线预览'
  if (previewMode.value === 'docx') return 'DOCX 在线预览'
  if (previewMode.value === 'text') return '文本预览'
  return '暂无预览'
})

watch(selectedKnowledgeBaseId, value => {
  if (!value) {
    kbFiles.value = []
    resetPreview()
    return
  }
  fetchKbFiles(value)
})

function syncPageFromHash() {
  const page = window.location.hash.replace('#/', '').replace('#', '') || 'kb'
  currentPage.value = navItems.some(item => item.key === page) ? page : 'kb'
  showTips.value = false
}

function goPage(page) {
  window.location.hash = `#/${page}`
}

function toggleTips() {
  showTips.value = !showTips.value
}

onMounted(async () => {
  syncPageFromHash()
  window.addEventListener('hashchange', syncPageFromHash)
  await fetchKnowledgeBases()
})

onBeforeUnmount(() => {
  window.removeEventListener('hashchange', syncPageFromHash)
  revokePreviewUrl()
})

function onKbFileChange(event) {
  kbFile.value = event.target.files?.[0] || null
}

function onTenderFileChange(event) {
  tenderFile.value = event.target.files?.[0] || null
}

async function fetchKnowledgeBases() {
  try {
    loading.kbList = true
    const { data } = await api.get('/api/kb')
    knowledgeBases.value = data.data || []
    if (!selectedKnowledgeBaseId.value && knowledgeBases.value.length) {
      selectedKnowledgeBaseId.value = knowledgeBases.value[0].id
    } else if (selectedKnowledgeBaseId.value && !knowledgeBases.value.some(item => item.id === selectedKnowledgeBaseId.value)) {
      selectedKnowledgeBaseId.value = knowledgeBases.value[0]?.id || ''
    }
  } catch (error) {
    kbActionResult.value = getErrorMessage(error)
  } finally {
    loading.kbList = false
  }
}

async function createKnowledgeBase() {
  try {
    loading.createKb = true
    const { data } = await api.post('/api/kb', { name: newKbName.value })
    kbActionResult.value = JSON.stringify(data, null, 2)
    newKbName.value = ''
    await fetchKnowledgeBases()
    if (data.data?.id) {
      selectedKnowledgeBaseId.value = data.data.id
    }
  } catch (error) {
    kbActionResult.value = getErrorMessage(error)
  } finally {
    loading.createKb = false
  }
}

function selectKnowledgeBase(id) {
  selectedKnowledgeBaseId.value = id
}

async function fetchKbFiles(id = selectedKnowledgeBaseId.value) {
  if (!id) return
  try {
    loading.kbFiles = true
    const { data } = await api.get(`/api/kb/${encodeURIComponent(id)}/files`)
    kbFiles.value = data.data || []
  } catch (error) {
    kbActionResult.value = getErrorMessage(error)
  } finally {
    loading.kbFiles = false
  }
}

async function uploadKbFile() {
  try {
    loading.kbUpload = true
    const formData = new FormData()
    formData.append('file', kbFile.value)
    const { data } = await api.post(`/api/kb/${encodeURIComponent(selectedKnowledgeBaseId.value)}/upload`, formData)
    kbActionResult.value = JSON.stringify(data, null, 2)
    kbFile.value = null
    await fetchKnowledgeBases()
    await fetchKbFiles()
  } catch (error) {
    kbActionResult.value = getErrorMessage(error)
  } finally {
    loading.kbUpload = false
  }
}

async function buildKnowledgeBase() {
  try {
    loading.kbBuild = true
    const { data } = await api.post('/api/kb/build', { knowledge_base_id: selectedKnowledgeBaseId.value, file_names: null })
    kbActionResult.value = JSON.stringify(data, null, 2)
  } catch (error) {
    kbActionResult.value = getErrorMessage(error)
  } finally {
    loading.kbBuild = false
  }
}

async function migrateLegacyKnowledgeBases() {
  try {
    loading.migrate = true
    const { data } = await api.post('/api/kb/migrate')
    kbActionResult.value = JSON.stringify(data, null, 2)
    await fetchKnowledgeBases()
  } catch (error) {
    kbActionResult.value = getErrorMessage(error)
  } finally {
    loading.migrate = false
  }
}

async function previewFile(file) {
  try {
    loading.kbPreview = true
    resetPreview(false)
    previewFileName.value = file.name

    if (file.suffix === '.pdf') {
      const response = await api.get(contentUrl(file.name), { responseType: 'blob' })
      previewMode.value = 'pdf'
      previewUrl.value = URL.createObjectURL(response.data)
      return
    }

    if (file.suffix === '.docx') {
      const response = await api.get(contentUrl(file.name), { responseType: 'arraybuffer' })
      const result = await mammoth.convertToHtml({ arrayBuffer: response.data })
      previewMode.value = 'docx'
      previewHtml.value = result.value || '<p>DOCX 内容为空</p>'
      return
    }

    const { data } = await api.get(`/api/kb/${encodeURIComponent(selectedKnowledgeBaseId.value)}/files/${encodeURIComponent(file.name)}/preview`, {
      responseType: 'text'
    })
    previewMode.value = 'text'
    previewText.value = data
  } catch (error) {
    previewMode.value = 'text'
    previewText.value = getErrorMessage(error)
  } finally {
    loading.kbPreview = false
  }
}

function contentUrl(fileName) {
  return `/api/kb/${encodeURIComponent(selectedKnowledgeBaseId.value)}/files/${encodeURIComponent(fileName)}/content`
}

function downloadUrl(fileName) {
  return `${api.defaults.baseURL}/api/kb/${encodeURIComponent(selectedKnowledgeBaseId.value)}/files/${encodeURIComponent(fileName)}/download`
}

function resetPreview(revoke = true) {
  if (revoke) revokePreviewUrl()
  previewFileName.value = ''
  previewMode.value = ''
  previewHtml.value = ''
  previewText.value = ''
}

function revokePreviewUrl() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
}

async function askQuestion() {
  try {
    loading.ask = true
    const payload = { knowledge_base_id: selectedKnowledgeBaseId.value, question: question.value, top_k: topK.value }
    const { data } = await api.post('/api/kb/ask', payload)
    qaResult.value = data.data || { answer: '', sources: [], chunks: [], score: [] }
  } catch (error) {
    qaResult.value = { answer: getErrorMessage(error), sources: [], chunks: [], score: [] }
  } finally {
    loading.ask = false
  }
}

async function parseTender() {
  try {
    loading.tender = true
    const formData = new FormData()
    formData.append('file', tenderFile.value)
    const { data } = await api.post('/api/tender/parse', formData)
    tenderResult.value = data.data
  } catch (error) {
    tenderResult.value = { error: getErrorMessage(error) }
  } finally {
    loading.tender = false
  }
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

function getErrorMessage(error) {
  return error?.response?.data?.detail || error?.message || '请求失败'
}
</script>
