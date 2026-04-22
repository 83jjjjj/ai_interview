<template>
  <div class="evaluation-container">
    <!-- 会话信息 -->
    <el-card class="session-card">
      <h2>面试评价</h2>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="岗位">{{ session.position }}</el-descriptions-item>
        <el-descriptions-item label="风格">{{ session.style }}</el-descriptions-item>
        <el-descriptions-item label="难度">{{ session.difficulty }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ session.status }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 面试进行中 -->
    <el-card v-if="!evaluation && session.status === '进行中'" class="eval-card">
      <div class="loading-section">
        <p class="loading-text">面试尚未结束</p>
        <el-button type="primary" @click="$router.push(`/interview/${route.params.id}`)">继续面试</el-button>
      </div>
    </el-card>

    <!-- 评价生成中 -->
    <el-card v-if="!evaluation && session.status !== '进行中'" class="eval-card">
      <div class="progress-section">
        <!-- 计时 -->
        <div class="timer">
          <span>已等待 {{ elapsedSeconds }} 秒</span>
          <span v-if="estimatedTotal > 0">，预计还需 {{ estimatedRemaining }} 秒</span>
        </div>

        <!-- 总进度条 -->
        <el-progress :percentage="overallProgress" :stroke-width="10" :format="() => `${currentStepText}`" style="margin: 16px 0" />

        <!-- 步骤 -->
        <el-steps :active="currentStep" finish-status="success">
          <el-step title="分析总体评价" :status="stepStatus(0)" />
          <el-step title="计算维度评分" :status="stepStatus(1)" />
          <el-step title="生成改进建议" :status="stepStatus(2)" />
        </el-steps>
      </div>

      <!-- 已解析的部分实时显示 -->
      <div v-if="partialEval.summary" class="partial-section">
        <el-divider />
        <h3>总体评价</h3>
        <p>{{ partialEval.summary }}</p>
      </div>

      <div v-if="partialEval.dimensions" class="partial-section">
        <el-divider />
        <h3>维度评分</h3>
        <div v-for="(score, name) in partialEval.dimensions" :key="name" class="dimension-item">
          <span class="dimension-name">{{ name }}</span>
          <el-progress :percentage="score" :stroke-width="18" :format="() => score" />
        </div>
      </div>

      <div v-if="partialEval.suggestions" class="partial-section">
        <el-divider />
        <h3>改进建议</h3>
        <p>{{ partialEval.suggestions }}</p>
      </div>
    </el-card>

    <!-- 评价内容（完整展示） -->
    <template v-if="evaluation">
      <el-card class="eval-card">
        <div class="score-section">
          <div class="overall-score">
            <span class="score-number">{{ evaluation.overall_score }}</span>
            <span class="score-label">总体评分</span>
          </div>
        </div>

        <!-- 维度评分雷达图 -->
        <div class="chart-section">
          <div ref="chartRef" style="width: 400px; height: 300px; margin: 0 auto"></div>
        </div>

        <el-divider />

        <h3>总体评价</h3>
        <p>{{ evaluation.summary }}</p>

        <el-divider />

        <h3>改进建议</h3>
        <p>{{ evaluation.suggestions }}</p>

        <el-divider />

        <h3>待改进问答</h3>
        <el-timeline v-if="evaluation.improvements.length > 0">
          <el-timeline-item
            v-for="(item, index) in evaluation.improvements"
            :key="index"
            :timestamp="'改进点 ' + (index + 1)"
          >
            {{ item }}
          </el-timeline-item>
        </el-timeline>
        <p v-else>暂无需要改进的地方</p>
      </el-card>
    </template>

    <div class="actions">
      <el-button @click="$router.push('/')">返回首页</el-button>
      <el-button type="primary" @click="$router.push('/history')">查看历史记录</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import api from '../api'

const route = useRoute()
const session = ref({})
const evaluation = ref(null)
const chartRef = ref(null)
let eventSource = null
let timerInterval = null

// 流式进度跟踪
const partialEval = reactive({ summary: null, dimensions: null, suggestions: null })
const currentStep = ref(-1)
const elapsedSeconds = ref(0)
const chunkCount = ref(0)
const estimatedTotal = ref(30) // 默认预估 30 秒

// 总进度百分比（0-100）
const overallProgress = computed(() => {
  if (currentStep.value < 0) return 5
  const base = currentStep.value * 30
  const minProgress = Math.min(base + 25, 95)
  return minProgress
})

const currentStepText = computed(() => {
  const texts = ['正在分析总体评价...', '正在计算维度评分...', '正在生成改进建议...', '即将完成...']
  if (currentStep.value < 0) return 'AI 正在思考...'
  return texts[Math.min(currentStep.value, 3)]
})

const estimatedRemaining = computed(() => {
  return Math.max(0, estimatedTotal.value - elapsedSeconds.value)
})

function stepStatus(step) {
  if (step < currentStep.value) return 'success'
  if (step === currentStep.value) return 'process'
  return 'wait'
}

onMounted(async () => {
  const sessionId = route.params.id

  try {
    const response = await api.get(`/api/interview/${sessionId}/detail`)
    session.value = response.data.session

    if (response.data.evaluation) {
      evaluation.value = response.data.evaluation
      await nextTick()
      renderChart(response.data.evaluation.dimensions)
      return
    }

    if (response.data.session.status === '进行中') {
      return
    }
  } catch {
    session.value = { position: '-', style: '-', difficulty: '-', status: '-' }
  }

  // 启动计时器
  timerInterval = setInterval(() => {
    elapsedSeconds.value++
  }, 1000)

  // SSE 流式生成评价
  const token = localStorage.getItem('access_token')
  eventSource = new EventSource(
    `/api/interview/${sessionId}/evaluation-stream?access_token=${token}`
  )

  let streamingContent = ''

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.done) {
      eventSource.close()
      clearInterval(timerInterval)
      api.get(`/api/interview/${sessionId}/detail`).then(async (res) => {
        evaluation.value = res.data.evaluation
        if (evaluation.value) {
          await nextTick()
          renderChart(evaluation.value.dimensions)
        }
      })
      return
    }

    streamingContent += data.content
    chunkCount.value++

    // 根据 chunk 数量动态调整预估时间
    if (chunkCount.value > 3 && elapsedSeconds.value > 2) {
      // 每秒大约收到 3-5 个 chunk，总 chunk 数约 30-60
      const chunksPerSec = chunkCount.value / elapsedSeconds.value
      const estimatedTotalChunks = 50
      estimatedTotal.value = Math.ceil(estimatedTotalChunks / chunksPerSec)
    }

    // 尝试解析已收到的 JSON
    tryParsePartial(streamingContent)
  }

  eventSource.onerror = () => {
    eventSource.close()
    clearInterval(timerInterval)
    api.get(`/api/interview/${sessionId}/detail`).then(async (res) => {
      if (res.data.evaluation) {
        evaluation.value = res.data.evaluation
        await nextTick()
        renderChart(evaluation.value.dimensions)
      }
    })
  }
})

function tryParsePartial(text) {
  // summary
  if (!partialEval.summary) {
    const m = text.match(/"summary"\s*:\s*"((?:[^"\\]|\\.)*)"/)
    if (m) {
      partialEval.summary = m[1].replace(/\\n/g, '\n').replace(/\\"/g, '"')
      currentStep.value = 1
    }
  }

  // dimensions
  if (!partialEval.dimensions) {
    const m = text.match(/"dimensions"\s*:\s*(\{[^}]+\})/)
    if (m) {
      try {
        partialEval.dimensions = JSON.parse(m[1])
        currentStep.value = 2
      } catch { /* 还没完整 */ }
    }
  }

  // suggestions
  if (!partialEval.suggestions) {
    const m = text.match(/"suggestions"\s*:\s*"((?:[^"\\]|\\.)*)"/)
    if (m) {
      partialEval.suggestions = m[1].replace(/\\n/g, '\n').replace(/\\"/g, '"')
      currentStep.value = 3
    }
  }
}

onUnmounted(() => {
  if (eventSource) eventSource.close()
  if (timerInterval) clearInterval(timerInterval)
})

function renderChart(dimensions) {
  if (!chartRef.value) return

  const chart = echarts.init(chartRef.value)
  const labels = Object.keys(dimensions)
  const values = Object.values(dimensions)

  chart.setOption({
    title: { text: '维度评分', left: 'center' },
    radar: {
      indicator: labels.map((label, i) => ({ name: `${label}(${values[i]}/100)`, max: 100 })),
    },
    series: [
      {
        type: 'radar',
        data: [{ value: values, name: '评分' }],
      },
    ],
  })
}
</script>

<style scoped>
.evaluation-container {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.session-card,
.eval-card {
  margin-bottom: 16px;
}

.progress-section {
  padding: 16px 0;
}

.timer {
  text-align: center;
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.partial-section {
  margin-top: 8px;
}

.loading-section {
  text-align: center;
  padding: 40px 0;
}

.loading-text {
  margin-top: 16px;
  color: #909399;
}

.score-section {
  text-align: center;
  margin: 24px 0;
}

.overall-score {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
}

.score-number {
  font-size: 48px;
  font-weight: bold;
  color: #409eff;
}

.score-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.dimensions-section {
  margin: 16px 0;
}

.dimension-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.dimension-name {
  width: 80px;
  font-size: 14px;
  color: #606266;
  flex-shrink: 0;
}

.actions {
  text-align: center;
  margin-top: 16px;
}
</style>
