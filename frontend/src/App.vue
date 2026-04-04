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

      <div class="workspace-switcher">
        <span class="switcher-label">当前工作区</span>
        <div class="switcher-card">
          <strong>默认业务空间</strong>
          <small>LangChain Tender MVP</small>
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
          <span>
            <strong>{{ item.label }}</strong>
            <small>{{ item.desc }}</small>
          </span>
          <em class="nav-badge">{{ item.short }}</em>
        </button>
      </nav>

      <div class="sidebar-footer">
        <div class="mini-title">系统状态</div>
        <div class="mini-card">
          <span>当前页面</span>
          <strong>{{ currentPageLabel }}</strong>
        </div>
        <div class="mini-card">
          <span>知识库来源</span>
          <strong>{{ qaResult.sources?.length || 0 }} 个</strong>
        </div>
        <div class="mini-card">
          <span>标书状态</span>
          <strong>{{ tenderFileName || '未上传' }}</strong>
        </div>
      </div>
    </aside>

    <div class="main-shell">
      <header class="topbar">
        <div class="topbar-main">
          <div class="breadcrumb">工作台 / {{ currentPageLabel }}</div>
          <div class="page-eyebrow">Enterprise Workspace</div>
          <h1>{{ currentPageMeta.title }}</h1>
          <p>{{ currentPageMeta.desc }}</p>
        </div>

        <div class="topbar-actions">
          <div class="top-stat">
            <span>知识库文件</span>
            <strong>{{ kbFileName || '未选择' }}</strong>
          </div>
          <div class="top-stat">
            <span>运行状态</span>
            <strong>{{ currentStatusText }}</strong>
          </div>
          <div class="top-stat highlight">
            <span>系统模式</span>
            <strong>业务处理</strong>
          </div>
        </div>
      </header>

      <section class="overview-strip">
        <div class="overview-card">
          <span>上传文档</span>
          <strong>{{ kbFileName || '暂无文件' }}</strong>
          <small>用于知识库构建</small>
        </div>
        <div class="overview-card">
          <span>问答片段</span>
          <strong>{{ qaResult.chunks?.length || 0 }} 段</strong>
          <small>当前命中的证据条数</small>
        </div>
        <div class="overview-card">
          <span>解析文件</span>
          <strong>{{ tenderFileName || '暂无文件' }}</strong>
          <small>标书解析输入源</small>
        </div>
        <div class="overview-card accent">
          <span>当前页面</span>
          <strong>{{ currentPageLabel }}</strong>
          <small>{{ currentPageMeta.title }}</small>
        </div>
      </section>

      <main class="content-area">
        <section v-if="currentPage === 'kb'" class="page-grid two-col refined-grid">
          <div class="panel hero-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Document Intake</div>
                <h2>知识库文档上传</h2>
                <div class="panel-subtext">适合上传制度文件、规范文档、项目资料等知识库来源文件。</div>
              </div>
              <span class="panel-pill">上传</span>
            </div>

            <div class="upload-stage">
              <label class="dropzone">
                <input type="file" @change="onKbFileChange" />
                <div class="dropzone-icon">⬆</div>
                <div class="dropzone-title">{{ kbFileName || '点击选择知识库文件' }}</div>
                <div class="dropzone-desc">支持 PDF / DOCX / TXT，上传后可直接进入知识库构建流程</div>
              </label>
            </div>

            <div class="feature-list">
              <div class="feature-item">
                <strong>多格式支持</strong>
                <span>兼容 pdf / docx / txt</span>
              </div>
              <div class="feature-item">
                <strong>统一上传入口</strong>
                <span>减少构建前的手动处理</span>
              </div>
              <div class="feature-item">
                <strong>适合演示</strong>
                <span>界面更像正式业务系统</span>
              </div>
            </div>

            <div class="form-actions">
              <button class="btn btn-primary" :disabled="!kbFile || loading.kbUpload" @click="uploadKbFile">
                {{ loading.kbUpload ? '上传中...' : '上传文档' }}
              </button>
            </div>
          </div>

          <div class="stack-panel">
            <div class="panel side-panel">
              <div class="panel-header">
                <div>
                  <div class="section-tag">Build Queue</div>
                  <h2>知识库构建控制台</h2>
                  <div class="panel-subtext">支持指定文件构建，或直接扫描 uploads 全量文件。</div>
                </div>
                <span class="panel-pill success">Build</span>
              </div>

              <div class="field">
                <label class="label">指定构建文件名（可选）</label>
                <input
                  v-model="buildFileNames"
                  type="text"
                  placeholder="例如：a.pdf,b.docx；为空则扫描 uploads 全部文件"
                />
              </div>

              <div class="dashboard-metrics compact-grid">
                <div class="metric-box">
                  <span>已选文件</span>
                  <strong>{{ kbFileName || '暂无' }}</strong>
                </div>
                <div class="metric-box">
                  <span>构建范围</span>
                  <strong>{{ buildFileNames ? '指定文件' : '全量扫描' }}</strong>
                </div>
              </div>

              <div class="form-actions">
                <button class="btn btn-secondary" :disabled="loading.kbBuild" @click="buildKnowledgeBase">
                  {{ loading.kbBuild ? '构建中...' : '构建知识库' }}
                </button>
              </div>
            </div>

            <div class="panel quick-panel">
              <div class="panel-header">
                <div>
                  <div class="section-tag">Process Tips</div>
                  <h2>操作建议</h2>
                </div>
                <span class="panel-pill neutral">Guide</span>
              </div>

              <ul class="timeline-list">
                <li>先上传原始资料，再执行构建。</li>
                <li>若只想更新部分文件，可指定文件名。</li>
                <li>构建完成后切换到“知识库问答”页验证效果。</li>
              </ul>
            </div>
          </div>

          <div class="panel full-span result-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">Execution Log</div>
                <h2>上传 / 构建结果</h2>
              </div>
              <span class="panel-pill neutral">JSON</span>
            </div>
            <pre class="code-block">{{ kbUploadResult }}</pre>
          </div>
        </section>

        <section v-else-if="currentPage === 'qa'" class="page-grid qa-layout refined-grid">
          <div class="panel qa-input-panel">
            <div class="panel-header">
              <div>
                <div class="section-tag">RAG Search</div>
                <h2>知识库问答</h2>
                <div class="panel-subtext">输入问题，查看回答结果，并校验引用来源与命中证据。</div>
              </div>
              <span class="panel-pill success">Ask</span>
            </div>

            <div class="field">
              <label class="label">问题输入</label>
              <textarea
                v-model="question"
                placeholder="请输入你的问题，例如：招标文件对交付周期、验收标准、售后服务有什么要求？"
              ></textarea>
            </div>

            <div class="inline-row">
              <div class="field field-small">
                <label class="label">Top K</label>
                <input v-model.number="topK" type="number" min="1" max="10" />
              </div>
              <div class="metric-box stretch">
                <span>命中文档来源</span>
                <strong>{{ qaResult.sources?.length || 0 }} 个</strong>
              </div>
              <div class="metric-box stretch">
                <span>命中片段</span>
                <strong>{{ qaResult.chunks?.length || 0 }} 段</strong>
              </div>
            </div>

            <div class="form-actions">
              <button class="btn btn-primary" :disabled="!question || loading.ask" @click="askQuestion">
                {{ loading.ask ? '提问中...' : '开始问答' }}
              </button>
            </div>
          </div>

          <div class="stack-panel">
            <div class="panel qa-answer-panel">
              <div class="panel-header">
                <div>
                  <div class="section-tag">Answer Board</div>
                  <h2>回答结果</h2>
                </div>
                <span class="panel-pill">Answer</span>
              </div>

              <div class="answer-board">{{ qaResult.answer || '暂无结果' }}</div>

              <div class="source-section" v-if="qaResult.sources?.length">
                <div class="sub-title">来源文件</div>
                <div class="tag-list">
                  <span class="tag" v-for="(item, index) in qaResult.sources" :key="index">{{ item }}</span>
                </div>
              </div>
            </div>

            <div class="panel quick-panel">
              <div class="panel-header">
                <div>
                  <div class="section-tag">Validation</div>
                  <h2>结果校验建议</h2>
                </div>
                <span class="panel-pill neutral">Check</span>
              </div>

              <ul class="timeline-list">
                <li>先确认回答是否包含明确结论。</li>
                <li>再检查来源文件是否符合预期。</li>
                <li>最后结合命中文本片段做人工复核。</li>
              </ul>
            </div>
          </div>

          <div class="panel full-span">
            <div class="panel-header">
              <div>
                <div class="section-tag">Evidence Panel</div>
                <h2>命中文本片段</h2>
              </div>
              <span class="panel-pill warning">{{ qaResult.chunks?.length || 0 }} 段</span>
            </div>

            <div v-if="qaResult.chunks?.length" class="chunk-list">
              <article class="chunk-card" v-for="(chunk, index) in qaResult.chunks" :key="index">
                <div class="chunk-card-top">
                  <span>片段 {{ index + 1 }}</span>
                  <strong>Score {{ qaResult.score?.[index] ?? '-' }}</strong>
                </div>
                <p>{{ chunk }}</p>
              </article>
            </div>
            <div v-else class="empty-state">暂无命中文本片段</div>
          </div>
        </section>

        <section v-else class="page-grid tender-layout refined-grid">
          <div class="stack-panel">
            <div class="panel tender-left">
              <div class="panel-header">
                <div>
                  <div class="section-tag">Tender Intake</div>
                  <h2>标书文件上传</h2>
                  <div class="panel-subtext">适合上传招标文件、技术规范、商务要求等需要结构化提取的资料。</div>
                </div>
                <span class="panel-pill accent">Tender</span>
              </div>

              <label class="dropzone tall">
                <input type="file" @change="onTenderFileChange" />
                <div class="dropzone-icon">📄</div>
                <div class="dropzone-title">{{ tenderFileName || '点击选择标书文件' }}</div>
                <div class="dropzone-desc">上传后执行解析接口，输出结构化 JSON 结果</div>
              </label>

              <div class="dashboard-metrics single-column">
                <div class="metric-box">
                  <span>当前文件</span>
                  <strong>{{ tenderFileName || '未选择' }}</strong>
                </div>
                <div class="metric-box">
                  <span>解析状态</span>
                  <strong>{{ loading.tender ? '解析中' : '待执行' }}</strong>
                </div>
              </div>

              <div class="form-actions">
                <button class="btn btn-primary" :disabled="!tenderFile || loading.tender" @click="parseTender">
                  {{ loading.tender ? '解析中...' : '上传并解析' }}
                </button>
              </div>
            </div>

            <div class="panel quick-panel">
              <div class="panel-header">
                <div>
                  <div class="section-tag">Usage Notes</div>
                  <h2>解析说明</h2>
                </div>
                <span class="panel-pill neutral">Note</span>
              </div>

              <ul class="timeline-list">
                <li>优先上传结构清晰的正式标书。</li>
                <li>若结果异常，建议先检查文档格式与内容质量。</li>
                <li>解析结果可作为后续摘要、比对、抽取的基础数据。</li>
              </ul>
            </div>
          </div>

          <div class="panel tender-right">
            <div class="panel-header">
              <div>
                <div class="section-tag">Structured Output</div>
                <h2>解析结果视图</h2>
              </div>
              <span class="panel-pill neutral">JSON</span>
            </div>

            <pre class="code-block tall-code">{{ tenderResultText }}</pre>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, reactive, ref } from 'vue'
import api from './api'

const navItems = [
  { key: 'kb', label: '知识库构建', desc: '上传、入库、构建', icon: '📚', short: 'KB' },
  { key: 'qa', label: '知识库问答', desc: 'RAG 检索问答', icon: '💬', short: 'QA' },
  { key: 'tender', label: '标书解析', desc: '结构化提取结果', icon: '🧾', short: 'TD' }
]

const pageMetaMap = {
  kb: {
    title: '知识库构建中心',
    desc: '把文档上传、指定构建范围、触发知识库生成都集中到一个正式工作页里。'
  },
  qa: {
    title: '知识库问答中心',
    desc: '把问题输入、答案输出、证据片段拆成标准工作区，更适合真实业务使用。'
  },
  tender: {
    title: '标书解析中心',
    desc: '单独为标书解析提供一页完整界面，左侧操作，右侧结果，避免交互混乱。'
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
}

function goPage(page) {
  window.location.hash = `#/${page}`
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
