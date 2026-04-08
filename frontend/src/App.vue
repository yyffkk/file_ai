<template>
  <div class="app-frame">
    <aside class="sidebar">
      <div class="brand-block">
        <div class="brand-logo">AI</div>
        <div>
          <div class="brand-name">TenderOS</div>
          <div class="brand-subtitle">统一文档工作台</div>
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
          <span>系统状态</span>
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
          <button class="tool-btn secondary" @click="refreshAll">刷新数据</button>
        </div>
      </header>

      <section v-if="showTips" class="tips-banner">
        <div class="tips-title">使用说明</div>
        <div class="tips-text">{{ currentPageMeta.tips }}</div>
      </section>

      <main class="content-area">
        <section v-if="currentPage === 'docs'" class="page-grid kb-layout">
          <div class="panel left-stack">
            <div class="panel-header">
              <div>
                <div class="section-tag">Document Center</div>
                <h2>统一文档入口</h2>
              </div>
              <span class="panel-pill">上传后可多处理</span>
            </div>

            <label class="upload-area compact-upload">
              <input type="file" @change="onDocumentFileChange" />
              <div class="upload-title small">{{ documentFileName || '点击选择文档' }}</div>
              <div class="upload-desc">支持 PDF / DOCX / TXT</div>
            </label>

            <div class="field">
              <label class="label">处理能力</label>
              <div class="checkbox-row">
                <label><input v-model="docForm.enableKb" type="checkbox" /> 加入知识库</label>
                <label><input v-model="docForm.enableParse" type="checkbox" /> 标书解析</label>
              </div>
            </div>

            <div class="field" v-if="docForm.enableKb">
              <label class="label">目标知识库</label>
              <select v-model="docForm.knowledgeBaseId" class="select-input">
                <option value="">请选择知识库</option>
                <option v-for="item in knowledgeBases" :key="item.id" :value="item.id">{{ item.name }}</option>
              </select>
            </div>

            <div class="action-row">
              <button class="primary-btn" :disabled="!documentFile || loading.documentUpload" @click="uploadUnifiedDocument">
                {{ loading.documentUpload ? '处理中...' : '上传并处理' }}
              </button>
            </div>
          </div>

          <div class="panel right-stack">
            <div class="panel-header">
              <div>
                <div class="section-tag">Status</div>
                <h2>文件状态列表</h2>
              </div>
              <span class="panel-pill subtle">{{ documents.length }} 个文件</span>
            </div>

            <div class="table-wrap">
              <table class="file-table">
                <thead>
                  <tr>
                    <th>文件</th>
                    <th>文件状态</th>
                    <th>知识库状态</th>
                    <th>解析状态</th>
                    <th>目标知识库</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in documents" :key="item.id">
                    <td>{{ item.name }}</td>
                    <td>{{ item.file_status }}</td>
                    <td>{{ item.knowledge_base_status }}</td>
                    <td>{{ item.parse_status }}</td>
                    <td>{{ kbNameById(item.knowledge_base_id) || '-' }}</td>
                  </tr>
                  <tr v-if="!documents.length">
                    <td colspan="5" class="empty-row">暂无文档</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="panel result-panel full-span">
            <div class="panel-header">
              <div>
                <div class="section-tag">Result</div>
                <h2>最近执行结果</h2>
              </div>
              <span class="panel-pill subtle">JSON</span>
            </div>
            <pre class="result-box light">{{ actionResult }}</pre>
          </div>
        </section>

        <section v-else-if="currentPage === 'kb'" class="page-grid kb-layout">
          <div class="panel left-stack">
            <div class="panel-header">
              <div>
                <div class="section-tag">Knowledge Base</div>
                <h2>知识库管理</h2>
              </div>
              <span class="panel-pill">{{ knowledgeBases.length }} 个</span>
            </div>

            <div class="field">
              <label class="label">新建知识库</label>
              <div class="inline-form">
                <input v-model="newKbName" type="text" placeholder="例如：招标模板库" />
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
                  <small>ID：{{ item.id }}</small>
                </div>
                <span>{{ item.build_status || '未构建' }}</span>
              </button>
            </div>
          </div>

          <div class="panel right-stack">
            <div class="panel-header">
              <div>
                <div class="section-tag">Build</div>
                <h2>知识库构建</h2>
              </div>
              <span class="panel-pill subtle">{{ selectedKbName || '未选择' }}</span>
            </div>

            <template v-if="selectedKnowledgeBaseId">
              <div class="kb-meta-strip">
                <div><span>知识库</span><strong>{{ selectedKbName }}</strong></div>
                <div><span>构建状态</span><strong>{{ selectedKbBuildStatus }}</strong></div>
                <div><span>文件数</span><strong>{{ kbFiles.length }}</strong></div>
              </div>

              <div class="action-row">
                <button class="primary-btn" :disabled="loading.kbBuild" @click="buildKnowledgeBase">
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
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in kbFiles" :key="item.name">
                      <td>{{ item.name }}</td>
                      <td>{{ item.suffix }}</td>
                      <td>{{ formatFileSize(item.size) }}</td>
                      <td>{{ formatDate(item.updated_at) }}</td>
                    </tr>
                    <tr v-if="!kbFiles.length">
                      <td colspan="4" class="empty-row">当前知识库暂无文件，请去文档中心上传并绑定。</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>

            <div v-else class="empty-state light-empty short-empty">请先选择知识库。</div>
          </div>
        </section>

        <section v-else-if="currentPage === 'qa'" class="page-grid qa-clean-layout">
          <div class="panel large-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Question</div>
                <h2>智能问答</h2>
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
              <textarea v-model="question" placeholder="请输入你的问题"></textarea>
            </div>

            <div class="compact-form-row">
              <div class="field no-margin">
                <label class="label">Top K</label>
                <input v-model.number="topK" type="number" min="1" max="10" />
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
            </div>
            <div class="answer-box light">{{ qaResult.answer || '暂无结果' }}</div>
          </div>
        </section>

        <section v-else-if="currentPage === 'parse'" class="page-grid two-col-soft">
          <div class="panel large-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Parse Tasks</div>
                <h2>文档解析任务</h2>
              </div>
            </div>

            <div class="table-wrap">
              <table class="file-table">
                <thead>
                  <tr>
                    <th>文件</th>
                    <th>解析状态</th>
                    <th>文件状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in parsedDocuments" :key="item.id">
                    <td>{{ item.name }}</td>
                    <td>{{ item.parse_status }}</td>
                    <td>{{ item.file_status }}</td>
                    <td><button class="link-btn" :disabled="item.parse_status !== '已完成'" @click="openParseResult(item)">查看结果</button></td>
                  </tr>
                  <tr v-if="!parsedDocuments.length">
                    <td colspan="4" class="empty-row">暂无解析任务，请去文档中心上传并勾选“标书解析”。</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="panel result-panel clean-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Parse Result</div>
                <h2>当前解析结果</h2>
              </div>
            </div>
            <pre class="result-box light tall-result">{{ parseResultText }}</pre>
          </div>
        </section>

        <section v-else class="page-grid two-col-soft">
          <div class="panel large-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Result List</div>
                <h2>解析结果列表</h2>
              </div>
            </div>

            <div class="kb-list">
              <button v-for="item in completedParsedDocuments" :key="item.id" class="kb-card" @click="openParseResult(item)">
                <div>
                  <strong>{{ item.name }}</strong>
                  <small>{{ formatDate(item.updated_at) }}</small>
                </div>
                <span>{{ item.parse_status }}</span>
              </button>
              <div v-if="!completedParsedDocuments.length" class="empty-state light-empty short-empty">暂无已完成的解析结果。</div>
            </div>
          </div>

          <div class="panel result-panel clean-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">JSON</div>
                <h2>结构化结果</h2>
              </div>
              <span class="panel-pill subtle">{{ currentParseResultName || '未选择' }}</span>
            </div>
            <pre class="result-box light tall-result">{{ parseResultText }}</pre>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import api from './api'

const navItems = [
  { key: 'docs', label: '文档中心', desc: '统一上传 + 文件状态', icon: '📄' },
  { key: 'kb', label: '知识库管理', desc: '构建状态管理', icon: '📚' },
  { key: 'qa', label: '智能问答', desc: '绑定知识库问答', icon: '💬' },
  { key: 'parse', label: '文档解析', desc: '解析任务视图', icon: '🧾' },
  { key: 'result', label: '解析结果', desc: '查看结构化输出', icon: '📋' }
]

const pageMetaMap = {
  docs: { title: '文档中心', desc: '一个入口上传文档，再决定进入知识库、解析，或两者同时。', tips: '上传时勾选处理能力。加入知识库后，文件会进入对应知识库；勾选标书解析后，会自动生成结构化结果。' },
  kb: { title: '知识库管理', desc: '保留现有知识库能力，只把上传入口前移到文档中心。', tips: '知识库页负责创建、查看、构建，不再重复承担上传入口。' },
  qa: { title: '智能问答', desc: '选择已完成构建的知识库进行问答。', tips: '优先使用构建状态为“已完成”的知识库。' },
  parse: { title: '文档解析', desc: '查看解析任务状态，不再单独上传。', tips: '解析入口统一来自文档中心。此页负责看任务，不负责再传一次文件。' },
  result: { title: '解析结果', desc: '集中查看结构化解析输出。', tips: '优先查看 parse_status 为“已完成”的文档结果。' }
}

const currentPage = ref('docs')
const showTips = ref(false)
const newKbName = ref('')
const selectedKnowledgeBaseId = ref('')
const question = ref('')
const topK = ref(4)
const documentFile = ref(null)
const documents = ref([])
const knowledgeBases = ref([])
const kbFiles = ref([])
const qaResult = ref({ answer: '', sources: [], chunks: [], score: [] })
const parseResult = ref(null)
const currentParseResultName = ref('')
const actionResult = ref('暂无结果')

const docForm = reactive({
  enableKb: true,
  enableParse: false,
  knowledgeBaseId: ''
})

const loading = reactive({
  kbList: false,
  kbFiles: false,
  createKb: false,
  kbBuild: false,
  migrate: false,
  ask: false,
  documentUpload: false,
  documents: false
})

const currentPageMeta = computed(() => pageMetaMap[currentPage.value] || pageMetaMap.docs)
const currentPageLabel = computed(() => navItems.find(item => item.key === currentPage.value)?.label || '文档中心')
const currentStatusText = computed(() => Object.values(loading).some(Boolean) ? '处理中' : '空闲')
const selectedKbName = computed(() => knowledgeBases.value.find(item => item.id === selectedKnowledgeBaseId.value)?.name || '')
const selectedKbBuildStatus = computed(() => knowledgeBases.value.find(item => item.id === selectedKnowledgeBaseId.value)?.build_status || '未构建')
const documentFileName = computed(() => documentFile.value?.name || '')
const parsedDocuments = computed(() => documents.value.filter(item => item.process_for_parse))
const completedParsedDocuments = computed(() => documents.value.filter(item => item.parse_status === '已完成'))
const parseResultText = computed(() => parseResult.value ? JSON.stringify(parseResult.value, null, 2) : '暂无结果')

watch(selectedKnowledgeBaseId, value => {
  docForm.knowledgeBaseId = value
  if (!value) {
    kbFiles.value = []
    return
  }
  fetchKbFiles(value)
})

function syncPageFromHash() {
  const page = window.location.hash.replace('#/', '').replace('#', '') || 'docs'
  currentPage.value = navItems.some(item => item.key === page) ? page : 'docs'
}

function goPage(page) {
  window.location.hash = `#/${page}`
}

function toggleTips() {
  showTips.value = !showTips.value
}

function kbNameById(id) {
  return knowledgeBases.value.find(item => item.id === id)?.name || id || ''
}

function onDocumentFileChange(event) {
  documentFile.value = event.target.files?.[0] || null
}

onMounted(async () => {
  syncPageFromHash()
  window.addEventListener('hashchange', syncPageFromHash)
  await refreshAll()
})

onBeforeUnmount(() => {
  window.removeEventListener('hashchange', syncPageFromHash)
})

async function refreshAll() {
  await Promise.all([fetchKnowledgeBases(), fetchDocuments()])
}

async function fetchKnowledgeBases() {
  try {
    loading.kbList = true
    const { data } = await api.get('/api/kb')
    knowledgeBases.value = data.data || []
    if (!selectedKnowledgeBaseId.value && knowledgeBases.value.length) {
      selectedKnowledgeBaseId.value = knowledgeBases.value[0].id
    }
  } catch (error) {
    actionResult.value = getErrorMessage(error)
  } finally {
    loading.kbList = false
  }
}

async function fetchDocuments() {
  try {
    loading.documents = true
    const { data } = await api.get('/api/documents')
    documents.value = data.data || []
  } catch (error) {
    actionResult.value = getErrorMessage(error)
  } finally {
    loading.documents = false
  }
}

async function createKnowledgeBase() {
  try {
    loading.createKb = true
    const { data } = await api.post('/api/kb', { name: newKbName.value })
    actionResult.value = JSON.stringify(data, null, 2)
    newKbName.value = ''
    await fetchKnowledgeBases()
  } catch (error) {
    actionResult.value = getErrorMessage(error)
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
    actionResult.value = getErrorMessage(error)
  } finally {
    loading.kbFiles = false
  }
}

async function uploadUnifiedDocument() {
  if (!docForm.enableKb && !docForm.enableParse) {
    actionResult.value = '至少选择一种处理能力'
    return
  }
  if (docForm.enableKb && !docForm.knowledgeBaseId) {
    actionResult.value = '已勾选加入知识库，请先选择目标知识库'
    return
  }
  try {
    loading.documentUpload = true
    const formData = new FormData()
    formData.append('file', documentFile.value)
    formData.append('enable_kb', String(docForm.enableKb))
    formData.append('enable_parse', String(docForm.enableParse))
    formData.append('knowledge_base_id', docForm.knowledgeBaseId || '')
    const { data } = await api.post('/api/documents/upload', formData)
    actionResult.value = JSON.stringify(data, null, 2)
    documentFile.value = null
    await refreshAll()
    if (docForm.enableKb && docForm.knowledgeBaseId) {
      selectedKnowledgeBaseId.value = docForm.knowledgeBaseId
      await fetchKbFiles(docForm.knowledgeBaseId)
    }
    if (data.data?.parse_result) {
      parseResult.value = data.data.parse_result
      currentParseResultName.value = data.data?.document?.name || ''
    }
  } catch (error) {
    actionResult.value = getErrorMessage(error)
  } finally {
    loading.documentUpload = false
  }
}

async function buildKnowledgeBase() {
  try {
    loading.kbBuild = true
    const { data } = await api.post('/api/kb/build', { knowledge_base_id: selectedKnowledgeBaseId.value, file_names: null })
    actionResult.value = JSON.stringify(data, null, 2)
    await refreshAll()
    await fetchKbFiles()
  } catch (error) {
    actionResult.value = getErrorMessage(error)
  } finally {
    loading.kbBuild = false
  }
}

async function migrateLegacyKnowledgeBases() {
  try {
    loading.migrate = true
    const { data } = await api.post('/api/kb/migrate')
    actionResult.value = JSON.stringify(data, null, 2)
    await fetchKnowledgeBases()
  } catch (error) {
    actionResult.value = getErrorMessage(error)
  } finally {
    loading.migrate = false
  }
}

async function askQuestion() {
  try {
    loading.ask = true
    const { data } = await api.post('/api/kb/ask', { knowledge_base_id: selectedKnowledgeBaseId.value, question: question.value, top_k: topK.value })
    qaResult.value = data.data || { answer: '', sources: [], chunks: [], score: [] }
  } catch (error) {
    qaResult.value = { answer: getErrorMessage(error), sources: [], chunks: [], score: [] }
  } finally {
    loading.ask = false
  }
}

async function openParseResult(item) {
  try {
    const { data } = await api.get(`/api/documents/${encodeURIComponent(item.id)}/parse-result`)
    parseResult.value = data.data
    currentParseResultName.value = item.name
    currentPage.value = 'result'
    window.location.hash = '#/result'
  } catch (error) {
    parseResult.value = { error: getErrorMessage(error) }
    currentParseResultName.value = item.name
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
