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
      <div class="loading-section">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <p class="loading-text">AI 正在生成评价...</p>
        <!-- 流式输出的原始 JSON（调试用，用户看到的是解析后的结构化内容） -->
        <div v-if="streamingContent" class="streaming-preview">
          <pre>{{ streamingContent }}</pre>
        </div>
      </div>
    </el-card>

    <!-- 评价内容 -->
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
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '../api'

const route = useRoute()
const session = ref({})
const evaluation = ref(null)
const streamingContent = ref('')
const chartRef = ref(null)
let eventSource = null

onMounted(async () => {
  const sessionId = route.params.id

  // 先加载会话信息
  try {
    const response = await api.get(`/api/interview/${sessionId}/detail`)
    session.value = response.data.session

    if (response.data.evaluation) {
      // 评价已存在（比如刷新页面），直接显示
      evaluation.value = response.data.evaluation
      await nextTick()
      renderChart(response.data.evaluation.dimensions)
      return
    }

    if (response.data.session.status === '进行中') {
      // 面试还在进行中，不启动 SSE
      return
    }
  } catch {
    session.value = { position: '-', style: '-', difficulty: '-', status: '-' }
  }

  // 评价不存在，通过 SSE 流式生成
  const token = localStorage.getItem('access_token')
  eventSource = new EventSource(
    `/api/interview/${sessionId}/evaluation-stream?access_token=${token}`
  )

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.done) {
      eventSource.close()
      // 评价生成完毕，重新加载详情
      api.get(`/api/interview/${sessionId}/detail`).then(async (res) => {
        evaluation.value = res.data.evaluation
        if (evaluation.value) {
          await nextTick()
          renderChart(evaluation.value.dimensions)
        }
      })
      return
    }

    // 逐字追加显示
    streamingContent.value += data.content
  }

  eventSource.onerror = () => {
    eventSource.close()
    // 出错时也尝试加载已有评价
    api.get(`/api/interview/${sessionId}/detail`).then(async (res) => {
      if (res.data.evaluation) {
        evaluation.value = res.data.evaluation
        await nextTick()
        renderChart(evaluation.value.dimensions)
      }
    })
  }
})

onUnmounted(() => {
  if (eventSource) eventSource.close()
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
        data: [
          {
            value: values,
            name: '评分',
          },
        ],
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

.loading-section {
  text-align: center;
  padding: 40px 0;
}

.loading-text {
  margin-top: 16px;
  color: #909399;
}

.streaming-preview {
  margin-top: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  text-align: left;
  max-height: 300px;
  overflow-y: auto;
}

.streaming-preview pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  color: #606266;
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
  margin: 24px 0;
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
