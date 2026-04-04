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
          <span>当前页面</span>
          <strong>{{ currentPageLabel }}</strong>
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
          <button class="tool-btn" @click="toggleTips">
            {{ showTips ? '隐藏说明' : '查看说明' }}
          </button>
          <button class="tool-btn secondary" @click="goPage('kb')">知识库构建</button>
          <button class="tool-btn secondary" @click="goPage('qa')">知识库问答</button>
          <button class="tool-btn secondary" @click="goPage('tender')">标书解析</button>
        </div>
      </header>

      <section v-if="showTips" class="tips-banner">
        <div class="tips-title">使用说明</div>
        <div class="tips-text">{{ currentPageMeta.tips }}</div>
      </section>

      <main class="content-area">
        <section v-if="currentPage === 'kb'" class="page-grid airy-grid two-col-soft">
          <div class="panel large-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Document Upload</div>
                <h2>上传知识库文档</h2>
              </div>
              <span class="panel-pill">上传</span>
            </div>

            <label class="upload-area">
              <input type="file" @change="onKbFileChange" />
              <div class="upload-title">{{ kbFileName || '点击选择知识库文件' }}</div>
              <div class="upload-desc">支持 PDF / DOCX / TXT</div>
            </label>

            <div class="action-row">
              <button class="primary-btn" :disabled="!kbFile || loading.kbUpload" @click="uploadKbFile">
                {{ loading.kbUpload ? '上传中...' : '上传文档' }}
              </button>
            </div>
          </div>

          <div class="panel slim-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Build</div>
                <h2>构建知识库</h2>
              </div>
              <span class="panel-pill subtle">执行</span>
            </div>

            <div class="field">
              <label class="label">指定文件名（可选）</label>
              <input
                v-model="buildFileNames"
                type="text"
                placeholder="例如：a.pdf,b.docx；为空则扫描 uploads 全部文件"
              />
            </div>

            <div class="info-card">
              <span>当前文件</span>
              <strong>{{ kbFileName || '未选择文件' }}</strong>
            </div>

            <div class="action-row">
              <button class="secondary-btn" :disabled="loading.kbBuild" @click="buildKnowledgeBase">
                {{ loading.kbBuild ? '构建中...' : '构建知识库' }}
              </button>
            </div>
          </div>

          <div class="panel full-span result-panel clean-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Result</div>
                <h2>执行结果</h2>
              </div>
              <span class="panel-pill subtle">JSON</span>
            </div>
            <pre class="result-box light">{{ kbUploadResult }}</pre>
          </div>
        </section>

        <section v-else-if="currentPage === 'qa'" class="page-grid airy-grid qa-clean-layout">
          <div class="panel large-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Question</div>
                <h2>输入问题</h2>
              </div>
              <span class="panel-pill">问答</span>
            </div>

            <div class="field">
              <label class="label">问题内容</label>
              <textarea
                v-model="question"
                placeholder="请输入你的问题，例如：招标文件对交付周期、验收标准、售后服务有什么要求？"
              ></textarea>
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
              <button class="primary-btn" :disabled="!question || loading.ask" @click="askQuestion">
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

        <section v-else class="page-grid airy-grid two-col-soft">
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
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import api from './api'

const navItems = [
  { key: 'kb', label: '知识库构建', desc: '上传与构建', icon: '📚' },
  { key: 'qa', label: '知识库问答', desc: 'RAG 问答', icon: '💬' },
  { key: 'tender', label: '标书解析', desc: '结构化解析', icon: '🧾' }
]

const pageMetaMap = {
  kb: {
    title: '知识库构建中心',
    desc: '上传文档并构建知识库，页面更简洁，减少干扰信息。',
    tips: '先上传文档，再执行构建。如果只想更新部分内容，可在指定文件名中填写目标文件。'
  },
  qa: {
    title: '知识库问答中心',
    desc: '输入问题并查看回答结果，同时校验来源文件和证据片段。',
    tips: '建议先看回答，再结合来源文件和命中文本片段做人工确认。'
  },
  tender: {
    title: '标书解析中心',
    desc: '上传标书后直接查看结构化结果，布局更清爽，便于阅读。',
    tips: '优先上传格式清晰的正式文档，解析结果更稳定。'
  }
}

const kbFile = ref(null)
const tenderFile = ref(null)
const buildFileNames = ref('')
const question = ref('')
const topK = ref(4)
const kbUploadResult = ref('暂无结果')
const qaResult = ref({ answer: '', sources: [], chunks: [], score: [] })
const tenderResult = ref(null)
const currentPage = ref('kb')
const showTips = ref(false)

const loading = reactive({
  kbUpload: false,
  kbBuild: false,
  ask: false,
  tender: false
})

const kbFileName = computed(() => kbFile.value?.name || '')
const tenderFileName = computed(() => tenderFile.value?.name || '')
const currentPageMeta = computed(() => pageMetaMap[currentPage.value] || pageMetaMap.kb)
const currentPageLabel = computed(() => navItems.find(item => item.key === currentPage.value)?.label || '知识库构建')
const currentStatusText = computed(() => {
  if (loading.kbUpload || loading.kbBuild || loading.ask || loading.tender) return '处理中'
  return '空闲'
})

const tenderResultText = computed(() => {
  if (!tenderResult.value) return '暂无结果'
  return JSON.stringify(tenderResult.value, null, 2)
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

onMounted(() => {
  syncPageFromHash()
  window.addEventListener('hashchange', syncPageFromHash)
})

onBeforeUnmount(() => {
  window.removeEventListener('hashchange', syncPageFromHash)
})

function onKbFileChange(event) {
  kbFile.value = event.target.files?.[0] || null
}

function onTenderFileChange(event) {
  tenderFile.value = event.target.files?.[0] || null
}

async function uploadKbFile() {
  try {
    loading.kbUpload = true
    const formData = new FormData()
    formData.append('file', kbFile.value)
    const { data } = await api.post('/api/kb/upload', formData)
    kbUploadResult.value = JSON.stringify(data, null, 2)
  } catch (error) {
    kbUploadResult.value = getErrorMessage(error)
  } finally {
    loading.kbUpload = false
  }
}

async function buildKnowledgeBase() {
  try {
    loading.kbBuild = true
    const fileNames = buildFileNames.value
      .split(',')
      .map(item => item.trim())
      .filter(Boolean)

    const payload = {
      file_names: fileNames.length ? fileNames : null
    }
    const { data } = await api.post('/api/kb/build', payload)
    kbUploadResult.value = JSON.stringify(data, null, 2)
  } catch (error) {
    kbUploadResult.value = getErrorMessage(error)
  } finally {
    loading.kbBuild = false
  }
}

async function askQuestion() {
  try {
    loading.ask = true
    const payload = { question: question.value, top_k: topK.value }
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

function getErrorMessage(error) {
  return error?.response?.data?.detail || error?.message || '请求失败'
}
</script>
