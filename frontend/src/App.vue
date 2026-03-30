<template>
  <div class="container">
    <div class="page-title">LangChain 知识库 + 标书解析</div>
    <div class="page-desc">Vue 3 极简交互界面，用于上传文档、构建知识库、问答和标书解析。</div>

    <div class="grid">
      <div class="card">
        <h2>知识库文档上传</h2>
        <div class="field">
          <label class="label">选择文件（pdf/docx/txt）</label>
          <input type="file" @change="onKbFileChange" />
        </div>
        <button :disabled="!kbFile || loading.kbUpload" @click="uploadKbFile">
          {{ loading.kbUpload ? '上传中...' : '上传文档' }}
        </button>
        <div class="field" style="margin-top: 14px">
          <label class="label">已上传文件名（可选，逗号分隔）</label>
          <input v-model="buildFileNames" type="text" placeholder="例如：a.pdf,b.docx；为空则扫描 uploads 全部文件" />
        </div>
        <button :disabled="loading.kbBuild" @click="buildKnowledgeBase">
          {{ loading.kbBuild ? '构建中...' : '构建知识库' }}
        </button>
        <div class="field" style="margin-top: 14px">
          <label class="label">结果</label>
          <div class="result-box">{{ kbUploadResult }}</div>
        </div>
      </div>

      <div class="card">
        <h2>知识库问答</h2>
        <div class="field">
          <label class="label">问题</label>
          <textarea v-model="question" placeholder="请输入你的问题"></textarea>
        </div>
        <div class="field">
          <label class="label">Top K</label>
          <input v-model.number="topK" type="number" min="1" max="10" />
        </div>
        <button :disabled="!question || loading.ask" @click="askQuestion">
          {{ loading.ask ? '提问中...' : '开始问答' }}
        </button>
        <div class="field" style="margin-top: 14px">
          <label class="label">回答</label>
          <div class="result-box">{{ qaResult.answer || '暂无结果' }}</div>
        </div>
        <div class="field" v-if="qaResult.sources?.length">
          <label class="label">来源文件</label>
          <div class="tag-list">
            <span class="tag" v-for="(item, index) in qaResult.sources" :key="index">{{ item }}</span>
          </div>
        </div>
      </div>

      <div class="card full" v-if="qaResult.chunks?.length">
        <h2>命中文本片段</h2>
        <div class="chunk-item" v-for="(chunk, index) in qaResult.chunks" :key="index">
          <div><strong>Score:</strong> {{ qaResult.score?.[index] ?? '' }}</div>
          <div style="margin-top: 8px">{{ chunk }}</div>
        </div>
      </div>

      <div class="card full">
        <h2>标书解析</h2>
        <div class="field">
          <label class="label">选择标书文件（pdf/docx/txt）</label>
          <input type="file" @change="onTenderFileChange" />
        </div>
        <button :disabled="!tenderFile || loading.tender" @click="parseTender">
          {{ loading.tender ? '解析中...' : '上传并解析' }}
        </button>
        <div class="field" style="margin-top: 14px">
          <label class="label">解析结果 JSON</label>
          <div class="result-box">{{ tenderResultText }}</div>
        </div>
      </div>
    </div>
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
