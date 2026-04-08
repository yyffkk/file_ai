<template>
  <div class="app-frame">
    <aside class="sidebar">
      <div class="brand-block">
        <div class="brand-logo">AI</div>
        <div>
          <div class="brand-name">TenderOS</div>
          <div class="brand-subtitle">AI 自主写标书工作台</div>
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
          <span>资料库</span>
          <strong>{{ selectedKbName || '未选择' }}</strong>
        </div>
      </div>
    </aside>

    <div class="main-shell">
      <header class="topbar">
        <div>
          <div class="breadcrumb">TenderOS / {{ currentPageLabel }}</div>
          <h1>{{ currentPageMeta.title }}</h1>
          <p>{{ currentPageMeta.desc }}</p>
        </div>
        <div class="topbar-actions compact-actions">
          <button class="tool-btn" @click="toggleTips">{{ showTips ? '隐藏说明' : '查看说明' }}</button>
          <button class="tool-btn secondary" @click="refreshAll">刷新数据</button>
          <button class="tool-btn primary-shortcut" @click="goPage('writer')">立即生成标书</button>
        </div>
      </header>

      <section v-if="showTips" class="tips-banner">
        <div class="tips-title">使用说明</div>
        <div class="tips-text">{{ currentPageMeta.tips }}</div>
      </section>

      <main class="content-area">
        <section v-if="currentPage === 'workbench'" class="page-grid two-col-soft">
          <div class="panel large-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Workbench</div>
                <h2>AI 写标书主流程</h2>
              </div>
              <span class="panel-pill">核心</span>
            </div>

            <div class="hero-box">
              <h3>资料入库后，直接驱动 AI 生成标书</h3>
              <p>上传企业资料、方案模板、案例、资质文件，进入资料库后即可作为 AI 写标书的参考来源。</p>
              <div class="action-row">
                <button class="primary-btn" @click="goPage('library')">先上传资料</button>
                <button class="secondary-btn" @click="goPage('writer')">开始写标书</button>
              </div>
            </div>

            <div class="compact-metrics">
              <div class="info-card grow"><span>资料文件</span><strong>{{ documents.length }}</strong></div>
              <div class="info-card grow"><span>资料库数量</span><strong>{{ knowledgeBases.length }}</strong></div>
              <div class="info-card grow"><span>生成结果</span><strong>{{ generatedResults.length }}</strong></div>
            </div>
          </div>

          <div class="panel result-panel clean-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Quick Start</div>
                <h2>推荐操作</h2>
              </div>
            </div>
            <div class="step-list">
              <div class="step-item"><strong>1</strong><span>上传资料到资料库</span></div>
              <div class="step-item"><strong>2</strong><span>构建资料库</span></div>
              <div class="step-item"><strong>3</strong><span>填写项目名称和需求</span></div>
              <div class="step-item"><strong>4</strong><span>让 AI 生成标书初稿</span></div>
            </div>
          </div>
        </section>

        <section v-else-if="currentPage === 'library'" class="page-grid kb-layout">
          <div class="panel left-stack">
            <div class="panel-header">
              <div>
                <div class="section-tag">Library Upload</div>
                <h2>上传资料</h2>
              </div>
              <span class="panel-pill">默认入库</span>
            </div>

            <div class="field">
              <label class="label">选择资料库</label>
              <select v-model="selectedKnowledgeBaseId" class="select-input">
                <option value="">请选择资料库</option>
                <option v-for="item in knowledgeBases" :key="item.id" :value="item.id">{{ item.name }}</option>
              </select>
            </div>

            <div class="field">
              <label class="label">新建资料库</label>
              <div class="inline-form">
                <input v-model="newKbName" type="text" placeholder="例如：公司资质库 / 过往案例库" />
                <button class="primary-btn" :disabled="!newKbName.trim() || loading.createKb" @click="createKnowledgeBase">
                  {{ loading.createKb ? '创建中...' : '新建' }}
                </button>
              </div>
            </div>

            <label class="upload-area compact-upload">
              <input type="file" @change="onDocumentFileChange" />
              <div class="upload-title small">{{ documentFileName || '点击选择资料文件' }}</div>
              <div class="upload-desc">上传后自动进入资料库，后续直接用于 AI 写标书</div>
            </label>

            <div class="action-row">
              <button class="primary-btn" :disabled="!documentFile || !selectedKnowledgeBaseId || loading.documentUpload" @click="uploadLibraryDocument">
                {{ loading.documentUpload ? '上传中...' : '上传资料' }}
              </button>
              <button class="secondary-btn" :disabled="!selectedKnowledgeBaseId || loading.kbBuild" @click="buildKnowledgeBase">
                {{ loading.kbBuild ? '构建中...' : '构建资料库' }}
              </button>
              <button class="secondary-btn" :disabled="!selectedKnowledgeBaseId" @click="goPage('writer')">去 AI 写标书</button>
            </div>
          </div>

          <div class="panel right-stack">
            <div class="panel-header">
              <div>
                <div class="section-tag">Library Files</div>
                <h2>资料状态</h2>
              </div>
              <span class="panel-pill subtle">{{ selectedKbName || '未选择' }}</span>
            </div>

            <div class="kb-meta-strip" v-if="selectedKnowledgeBaseId">
              <div><span>资料库</span><strong>{{ selectedKbName }}</strong></div>
              <div><span>状态</span><strong>{{ selectedKbBuildStatus }}</strong></div>
              <div><span>文件数</span><strong>{{ kbFiles.length }}</strong></div>
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
                    <td colspan="4" class="empty-row">当前资料库暂无文件，请先上传资料。</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section v-else-if="currentPage === 'writer'" class="page-grid kb-layout">
          <div class="panel large-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">AI Tender Writer</div>
                <h2>AI 写标书</h2>
              </div>
              <span class="panel-pill">主功能</span>
            </div>

            <div class="field">
              <label class="label">项目名称</label>
              <input v-model="writerForm.projectName" type="text" placeholder="例如：XX 信息化建设项目投标文件" />
            </div>

            <div class="field">
              <label class="label">招标需求文件</label>
              <label class="upload-area compact-upload requirement-upload">
                <input type="file" @change="onRequirementFileChange" />
                <div class="upload-title small">{{ writerForm.requirementFileName || requirementFile?.name || '点击上传招标需求文件' }}</div>
                <div class="upload-desc">支持 PDF / DOCX / TXT，上传后自动抽取文本</div>
              </label>
              <div class="action-row">
                <button class="secondary-btn" :disabled="!requirementFile || loading.uploadRequirement" @click="uploadRequirementFile">
                  {{ loading.uploadRequirement ? '抽取中...' : '导入需求文件' }}
                </button>
              </div>
            </div>

            <div class="field">
              <label class="label">招标需求文本</label>
              <textarea v-model="writerForm.requirementText" placeholder="可直接粘贴需求，也可先上传需求文件自动抽取文本。"></textarea>
            </div>

            <div class="field">
              <label class="label">选择资料库</label>
              <select v-model="writerForm.knowledgeBaseId" class="select-input">
                <option value="">请选择资料库</option>
                <option v-for="item in knowledgeBases" :key="item.id" :value="item.id">{{ item.name }}</option>
              </select>
            </div>

            <div class="compact-form-row">
              <div class="field no-margin">
                <label class="label">参考片段数量</label>
                <input v-model.number="writerForm.topK" type="number" min="1" max="10" />
              </div>
              <div class="info-card grow">
                <span>当前资料库</span>
                <strong>{{ kbNameById(writerForm.knowledgeBaseId) || '未选择' }}</strong>
              </div>
            </div>

            <div class="action-row">
              <button class="primary-btn" :disabled="!canGenerate || loading.generateTender" @click="generateTender">
                {{ loading.generateTender ? '生成中...' : '开始生成标书' }}
              </button>
            </div>
          </div>

          <div class="panel result-panel clean-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Generation Preview</div>
                <h2>生成预览</h2>
              </div>
            </div>
            <div class="answer-box light writer-preview">{{ generatedDraft.content || '生成后这里会显示标书初稿预览。' }}</div>
          </div>
        </section>

        <section v-else class="page-grid kb-layout">
          <div class="panel left-stack">
            <div class="panel-header">
              <div>
                <div class="section-tag">Generated Results</div>
                <h2>生成结果</h2>
              </div>
              <span class="panel-pill">可编辑</span>
            </div>

            <div class="kb-list">
              <button v-for="item in generatedResults" :key="item.id" class="kb-card" :class="{ active: currentResultId === item.id }" @click="openGeneratedResult(item.id)">
                <div>
                  <strong>{{ item.project_name }}</strong>
                  <small>{{ formatDate(item.updated_at) }}</small>
                </div>
                <span>{{ kbNameById(item.knowledge_base_id) || '资料库' }}</span>
              </button>
              <div v-if="!generatedResults.length" class="empty-state light-empty short-empty">还没有生成结果，先去“AI写标书”生成一份初稿。</div>
            </div>
          </div>

          <div class="panel right-stack">
            <div class="panel-header">
              <div>
                <div class="section-tag">Editor</div>
                <h2>结果编辑</h2>
              </div>
              <span class="panel-pill subtle">{{ resultEditor.projectName || '未选择' }}</span>
            </div>

            <div class="field">
              <label class="label">项目名称</label>
              <input v-model="resultEditor.projectName" type="text" placeholder="项目名称" />
            </div>

            <div class="field">
              <label class="label">标书内容</label>
              <textarea v-model="resultEditor.content" class="editor-area" placeholder="生成后的标书内容会显示在这里，支持继续编辑优化。"></textarea>
            </div>

            <div class="action-row">
              <button class="primary-btn" :disabled="!resultEditor.projectName || !resultEditor.content || !resultEditor.knowledgeBaseId || loading.saveResult" @click="saveGeneratedResult">
                {{ loading.saveResult ? '保存中...' : '保存结果' }}
              </button>
              <button class="secondary-btn" disabled>导出功能预留</button>
            </div>
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
  { key: 'workbench', label: '工作台', desc: 'AI 写标书主流程', icon: '🏠' },
  { key: 'library', label: '资料库', desc: '上传资料并入库', icon: '📚' },
  { key: 'writer', label: 'AI写标书', desc: '核心生成页面', icon: '✍️' },
  { key: 'result', label: '生成结果', desc: '查看与编辑结果', icon: '📄' }
]

const pageMetaMap = {
  workbench: { title: '工作台', desc: 'TenderOS 的核心目标是基于资料库，让 AI 自动生成标书初稿。', tips: '推荐路径：上传资料 → 构建资料库 → AI 写标书 → 编辑结果。' },
  library: { title: '资料库', desc: '上传资料后自动进入资料库，供 AI 写标书时统一参考。', tips: '这里不强调内部技术概念，只把资料准备好即可。' },
  writer: { title: 'AI 写标书', desc: '填写项目与需求，选择资料库后直接生成标书初稿。', tips: '项目名称和需求越清晰，生成结果越稳定。' },
  result: { title: '生成结果', desc: '查看、编辑、沉淀 AI 生成的标书初稿。', tips: '导出功能现阶段先预留，先保证生成与编辑链路可用。' }
}

const currentPage = ref('workbench')
const showTips = ref(false)
const newKbName = ref('')
const selectedKnowledgeBaseId = ref('')
const documentFile = ref(null)
const documents = ref([])
const knowledgeBases = ref([])
const kbFiles = ref([])
const generatedResults = ref([])
const generatedDraft = ref({})
const currentResultId = ref('')
const actionResult = ref('暂无结果')

const writerForm = reactive({
  projectName: '',
  requirementText: '',
  requirementFileName: '',
  knowledgeBaseId: '',
  topK: 6
})

const resultEditor = reactive({
  projectName: '',
  content: '',
  knowledgeBaseId: ''
})

const requirementFile = ref(null)

const loading = reactive({
  kbList: false,
  kbFiles: false,
  createKb: false,
  kbBuild: false,
  migrate: false,
  documentUpload: false,
  documents: false,
  uploadRequirement: false,
  generateTender: false,
  saveResult: false,
  generatedResults: false
})

const currentPageMeta = computed(() => pageMetaMap[currentPage.value] || pageMetaMap.workbench)
const currentPageLabel = computed(() => navItems.find(item => item.key === currentPage.value)?.label || '工作台')
const currentStatusText = computed(() => Object.values(loading).some(Boolean) ? '处理中' : '空闲')
const selectedKbName = computed(() => knowledgeBases.value.find(item => item.id === selectedKnowledgeBaseId.value)?.name || '')
const selectedKbBuildStatus = computed(() => knowledgeBases.value.find(item => item.id === selectedKnowledgeBaseId.value)?.build_status || '未构建')
const documentFileName = computed(() => documentFile.value?.name || '')
const canGenerate = computed(() => writerForm.projectName && writerForm.knowledgeBaseId)

watch(selectedKnowledgeBaseId, value => {
  if (!value) {
    kbFiles.value = []
    return
  }
  fetchKbFiles(value)
})

function syncPageFromHash() {
  const page = window.location.hash.replace('#/', '').replace('#', '') || 'workbench'
  currentPage.value = navItems.some(item => item.key === page) ? page : 'workbench'
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

function onRequirementFileChange(event) {
  requirementFile.value = event.target.files?.[0] || null
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
  await Promise.all([fetchKnowledgeBases(), fetchDocuments(), fetchGeneratedResults()])
}

async function fetchKnowledgeBases() {
  try {
    loading.kbList = true
    const { data } = await api.get('/api/kb')
    knowledgeBases.value = data.data || []
    if (!selectedKnowledgeBaseId.value && knowledgeBases.value.length) {
      selectedKnowledgeBaseId.value = knowledgeBases.value[0].id
    }
    if (!writerForm.knowledgeBaseId && knowledgeBases.value.length) {
      writerForm.knowledgeBaseId = knowledgeBases.value[0].id
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

async function fetchGeneratedResults() {
  try {
    loading.generatedResults = true
    const { data } = await api.get('/api/tender-writer/results')
    generatedResults.value = data.data || []
  } catch (error) {
    actionResult.value = getErrorMessage(error)
  } finally {
    loading.generatedResults = false
  }
}

async function createKnowledgeBase() {
  try {
    loading.createKb = true
    const { data } = await api.post('/api/kb', { name: newKbName.value })
    actionResult.value = JSON.stringify(data, null, 2)
    newKbName.value = ''
    await fetchKnowledgeBases()
    if (data.data?.id) {
      selectedKnowledgeBaseId.value = data.data.id
      writerForm.knowledgeBaseId = data.data.id
    }
  } catch (error) {
    actionResult.value = getErrorMessage(error)
  } finally {
    loading.createKb = false
  }
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

async function uploadLibraryDocument() {
  if (!selectedKnowledgeBaseId.value) {
    actionResult.value = '请先选择资料库'
    return
  }
  try {
    loading.documentUpload = true
    const formData = new FormData()
    formData.append('file', documentFile.value)
    formData.append('enable_kb', 'true')
    formData.append('enable_parse', 'false')
    formData.append('knowledge_base_id', selectedKnowledgeBaseId.value)
    const { data } = await api.post('/api/documents/upload', formData)
    actionResult.value = JSON.stringify(data, null, 2)
    documentFile.value = null
    await refreshAll()
    await fetchKbFiles(selectedKnowledgeBaseId.value)
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

async function uploadRequirementFile() {
  if (!requirementFile.value) {
    actionResult.value = '请先选择需求文件'
    return
  }
  try {
    loading.uploadRequirement = true
    const formData = new FormData()
    formData.append('file', requirementFile.value)
    const { data } = await api.post('/api/tender-writer/requirement-upload', formData)
    writerForm.requirementText = data.data?.text || ''
    writerForm.requirementFileName = data.data?.file_name || requirementFile.value.name
    actionResult.value = JSON.stringify(data, null, 2)
  } catch (error) {
    actionResult.value = getErrorMessage(error)
  } finally {
    loading.uploadRequirement = false
  }
}

async function generateTender() {
  try {
    loading.generateTender = true
    const payload = {
      project_name: writerForm.projectName,
      requirement_text: writerForm.requirementText,
      knowledge_base_id: writerForm.knowledgeBaseId,
      top_k: writerForm.topK
    }
    const { data } = await api.post('/api/tender-writer/generate', payload)
    generatedDraft.value = data.data || {}
    resultEditor.projectName = data.data?.project_name || writerForm.projectName
    resultEditor.content = data.data?.content || ''
    resultEditor.knowledgeBaseId = data.data?.knowledge_base_id || writerForm.knowledgeBaseId
    currentPage.value = 'result'
    window.location.hash = '#/result'
  } catch (error) {
    actionResult.value = getErrorMessage(error)
  } finally {
    loading.generateTender = false
  }
}

async function saveGeneratedResult() {
  try {
    loading.saveResult = true
    const payload = {
      project_name: resultEditor.projectName,
      content: resultEditor.content,
      knowledge_base_id: resultEditor.knowledgeBaseId
    }
    const { data } = await api.post('/api/tender-writer/results', payload)
    actionResult.value = JSON.stringify(data, null, 2)
    currentResultId.value = data.data?.id || ''
    await fetchGeneratedResults()
  } catch (error) {
    actionResult.value = getErrorMessage(error)
  } finally {
    loading.saveResult = false
  }
}

async function openGeneratedResult(id) {
  try {
    const { data } = await api.get(`/api/tender-writer/results/${encodeURIComponent(id)}`)
    currentResultId.value = id
    resultEditor.projectName = data.data?.project_name || ''
    resultEditor.content = data.data?.content || ''
    resultEditor.knowledgeBaseId = data.data?.knowledge_base_id || ''
  } catch (error) {
    actionResult.value = getErrorMessage(error)
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
