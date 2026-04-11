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

      <div class="sidebar-panel-group">
        <div class="sidebar-section nav-section">
          <div class="section-head">
            <h3>功能导航</h3>
          </div>
          <div class="nav-list">
            <button class="nav-item" :class="{ active: currentPage === 'library' }" @click="currentPage = 'library'">
              <div>
                <strong>我的知识库</strong>
                <small>管理知识库与知识库文件</small>
              </div>
            </button>
            <button class="nav-item" :class="{ active: currentPage === 'agent' }" @click="currentPage = 'agent'">
              <div>
                <strong>Agent 助手</strong>
                <small>原 AI 自动写标书，后续可接 Agent 工作流</small>
              </div>
            </button>
            <button class="nav-item" :class="{ active: currentPage === 'record' }" @click="currentPage = 'record'">
              <div>
                <strong>AI 记录</strong>
                <small>沉淀和保存 Agent 助手输出结果</small>
              </div>
            </button>
          </div>
        </div>

        <div v-if="currentPage === 'library'" class="sidebar-section kb-section">
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
              <div class="kb-item-main">
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
      </div>
    </aside>

    <main class="main-content">
      <template v-if="currentPage === 'library'">
        <header class="topbar">
          <div>
            <p class="eyebrow">Knowledge Base Center</p>
            <h1>{{ selectedKbName || '我的知识库' }}</h1>
            <p class="top-desc">
              当前页面只保留知识库文件管理和构建状态展示，不再展示无用的问答和统计区块。
            </p>
          </div>
        </header>

        <section class="summary-grid summary-grid-compact">
          <div class="summary-card">
            <span>当前知识库</span>
            <strong>{{ selectedKbName || '未选择' }}</strong>
          </div>
          <div class="summary-card">
            <span>构建状态</span>
            <strong>{{ selectedKbBuildStatus }}</strong>
          </div>
        </section>

        <section class="workspace-grid library-workspace-grid">
          <div class="panel full-span">
            <div class="panel-header">
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

          <div class="panel preview-panel full-span">
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
        </section>
      </template>

      <template v-else-if="currentPage === 'agent'">
        <header class="topbar writer-topbar">
          <div>
            <p class="eyebrow">Agent Assistant</p>
            <h1>Agent 助手</h1>
            <p class="top-desc">
              这里承接原“AI 自动写标书”能力，后续可以继续接入 Agent 工作流、LangGraph 和自动生成流程。
            </p>
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
        <header class="topbar writer-topbar">
          <div>
            <p class="eyebrow">AI Record</p>
            <h1>AI 记录</h1>
            <p class="top-desc">
              用于记录和沉淀 Agent 助手输出过的内容。用户如果需要保存答案、做二次整理或留档，后续可以统一放在这里。
            </p>
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
