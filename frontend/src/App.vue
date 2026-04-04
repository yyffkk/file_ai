<template>
  <div class="app-shell">
    <div class="bg-orb bg-orb-a"></div>
    <div class="bg-orb bg-orb-b"></div>

    <main class="container">
      <section class="hero">
        <div class="hero-copy">
          <div class="eyebrow">LangChain Tender MVP</div>
          <h1>知识库问答 + 标书解析<br />一个页面全搞定</h1>
          <p class="hero-desc">
            把上传、构建、问答、解析整合成一套更清晰的工作台，页面不再像测试页，拿给人演示也不会太寒酸。
          </p>

          <div class="hero-metrics">
            <div class="metric-card">
              <span class="metric-label">知识库文件</span>
              <strong>{{ kbFileName || '未选择' }}</strong>
            </div>
            <div class="metric-card">
              <span class="metric-label">标书文件</span>
              <strong>{{ tenderFileName || '未选择' }}</strong>
            </div>
            <div class="metric-card">
              <span class="metric-label">问答命中</span>
              <strong>{{ qaResult.sources?.length || 0 }} 个来源</strong>
            </div>
          </div>
        </div>

        <div class="hero-panel">
          <div class="panel-title">当前工作流</div>
          <div class="step-list">
            <div class="step-item active">
              <span>01</span>
              <div>
                <strong>上传文档</strong>
                <p>支持 pdf / docx / txt</p>
              </div>
            </div>
            <div class="step-item">
              <span>02</span>
              <div>
                <strong>构建知识库</strong>
                <p>支持指定文件或扫描 uploads</p>
              </div>
            </div>
            <div class="step-item">
              <span>03</span>
              <div>
                <strong>发起问答 / 解析标书</strong>
                <p>统一在右侧结果区查看输出</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="grid-layout">
        <div class="card feature-card">
          <div class="card-header">
            <div>
              <div class="card-kicker">Workspace A</div>
              <h2>知识库构建</h2>
            </div>
            <span class="status-chip">文档入库</span>
          </div>

          <div class="field">
            <label class="label">选择文件（pdf/docx/txt）</label>
            <label class="upload-box">
              <input type="file" @change="onKbFileChange" />
              <span class="upload-title">{{ kbFileName || '点击选择知识库文件' }}</span>
              <span class="upload-hint">上传后可继续指定文件名构建，或扫描 uploads 全部文件</span>
            </label>
          </div>

          <div class="action-row">
            <button class="primary-btn" :disabled="!kbFile || loading.kbUpload" @click="uploadKbFile">
              {{ loading.kbUpload ? '上传中...' : '上传文档' }}
            </button>
          </div>

          <div class="field">
            <label class="label">指定构建文件名（可选，逗号分隔）</label>
            <input
              v-model="buildFileNames"
              type="text"
              placeholder="例如：a.pdf,b.docx；为空则扫描 uploads 全部文件"
            />
          </div>

          <div class="action-row">
            <button class="ghost-btn" :disabled="loading.kbBuild" @click="buildKnowledgeBase">
              {{ loading.kbBuild ? '构建中...' : '构建知识库' }}
            </button>
          </div>

          <div class="result-panel compact">
            <div class="result-header">
              <span>执行结果</span>
              <span class="result-badge">KB</span>
            </div>
            <pre class="result-box">{{ kbUploadResult }}</pre>
          </div>
        </div>

        <div class="card feature-card">
          <div class="card-header">
            <div>
              <div class="card-kicker">Workspace B</div>
              <h2>知识库问答</h2>
            </div>
            <span class="status-chip success">RAG</span>
          </div>

          <div class="field">
            <label class="label">问题</label>
            <textarea v-model="question" placeholder="请输入你的问题，例如：招标文件对交付周期有哪些要求？"></textarea>
          </div>

          <div class="inline-fields">
            <div class="field">
              <label class="label">Top K</label>
              <input v-model.number="topK" type="number" min="1" max="10" />
            </div>
            <div class="field stat-box">
              <span class="stat-label">当前来源数</span>
              <strong>{{ qaResult.sources?.length || 0 }}</strong>
            </div>
          </div>

          <div class="action-row">
            <button class="primary-btn" :disabled="!question || loading.ask" @click="askQuestion">
              {{ loading.ask ? '提问中...' : '开始问答' }}
            </button>
          </div>

          <div class="result-panel">
            <div class="result-header">
              <span>回答结果</span>
              <span class="result-badge success">Answer</span>
            </div>
            <div class="answer-box">{{ qaResult.answer || '暂无结果' }}</div>
          </div>

          <div class="field" v-if="qaResult.sources?.length">
            <label class="label">来源文件</label>
            <div class="tag-list">
              <span class="tag" v-for="(item, index) in qaResult.sources" :key="index">{{ item }}</span>
            </div>
          </div>
        </div>

        <div class="card full-width" v-if="qaResult.chunks?.length">
          <div class="card-header">
            <div>
              <div class="card-kicker">Evidence</div>
              <h2>命中文本片段</h2>
            </div>
            <span class="status-chip warning">{{ qaResult.chunks.length }} 段</span>
          </div>

          <div class="chunk-grid">
            <div class="chunk-item" v-for="(chunk, index) in qaResult.chunks" :key="index">
              <div class="chunk-top">
                <span>片段 {{ index + 1 }}</span>
                <strong>Score {{ qaResult.score?.[index] ?? '-' }}</strong>
              </div>
              <p>{{ chunk }}</p>
            </div>
          </div>
        </div>

        <div class="card full-width tender-card">
          <div class="card-header">
            <div>
              <div class="card-kicker">Workspace C</div>
              <h2>标书解析</h2>
            </div>
            <span class="status-chip accent">Tender</span>
          </div>

          <div class="tender-layout">
            <div>
              <div class="field">
                <label class="label">选择标书文件（pdf/docx/txt）</label>
                <label class="upload-box large">
                  <input type="file" @change="onTenderFileChange" />
                  <span class="upload-title">{{ tenderFileName || '点击选择标书文件' }}</span>
                  <span class="upload-hint">上传后自动调用解析接口，结果以格式化 JSON 展示</span>
                </label>
              </div>

              <div class="action-row">
                <button class="primary-btn" :disabled="!tenderFile || loading.tender" @click="parseTender">
                  {{ loading.tender ? '解析中...' : '上传并解析' }}
                </button>
              </div>
            </div>

            <div class="result-panel tender-result">
              <div class="result-header">
                <span>解析结果 JSON</span>
                <span class="result-badge accent">JSON</span>
              </div>
              <pre class="result-box">{{ tenderResultText }}</pre>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import api from './api'

const kbFile = ref(null)
const tenderFile = ref(null)
const buildFileNames = ref('')
const question = ref('')
const topK = ref(4)
const kbUploadResult = ref('暂无结果')
const qaResult = ref({ answer: '', sources: [], chunks: [], score: [] })
const tenderResult = ref(null)

const loading = reactive({
  kbUpload: false,
  kbBuild: false,
  ask: false,
  tender: false
})

const kbFileName = computed(() => kbFile.value?.name || '')
const tenderFileName = computed(() => tenderFile.value?.name || '')

const tenderResultText = computed(() => {
  if (!tenderResult.value) return '暂无结果'
  return JSON.stringify(tenderResult.value, null, 2)
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
