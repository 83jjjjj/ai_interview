<template>
  <div class="analysis-container">
    <el-card>
      <div class="header">
        <h2>个人能力分析</h2>
        <el-button @click="$router.push('/')" size="small">返回首页</el-button>
      </div>

      <!-- 加载中 -->
      <div v-if="loading && !analysis" v-loading="true" style="min-height: 200px" />

      <!-- 无数据 -->
      <el-empty v-if="analysis && analysis.total_interviews === 0" description="暂无面试记录，请先完成面试" />

      <!-- 有数据 -->
      <template v-if="analysis && analysis.total_interviews > 0">
        <!-- 基础统计 -->
        <div class="stats-section">
          <el-statistic title="面试次数" :value="analysis.total_interviews" />
          <el-statistic title="平均分" :value="analysis.average_score" :precision="1" />
        </div>

        <!-- 能力趋势折线图 -->
        <div class="chart-section">
          <h3>能力趋势</h3>
          <div ref="chartRef" style="width: 100%; height: 350px"></div>
        </div>

        <el-divider />

        <!-- 优势/不足 — 始终显示，内容流式填入 -->
        <div class="summary-section">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-card shadow="never" class="summary-card strength">
                <h3>优势</h3>
                <p v-if="analysis.strength">{{ analysis.strength }}</p>
                <p v-else class="placeholder-text">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  AI 正在分析...
                </p>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card shadow="never" class="summary-card weakness">
                <h3>不足</h3>
                <p v-if="analysis.weakness">{{ analysis.weakness }}</p>
                <p v-else class="placeholder-text">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  AI 正在分析...
                </p>
              </el-card>
            </el-col>
          </el-row>
        </div>

        <el-divider />

        <!-- 发展建议 — 始终显示，内容流式填入 -->
        <div class="plan-section">
          <h3>发展建议</h3>
          <p v-if="analysis.development_plan">{{ analysis.development_plan }}</p>
          <p v-else class="placeholder-text">
            <el-icon class="is-loading"><Loading /></el-icon>
            AI 正在分析...
          </p>
        </div>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '../api'

const analysis = ref(null)
const loading = ref(true)
const chartRef = ref(null)
const streamingContent = ref('')
let eventSource = null

onMounted(async () => {
  const token = localStorage.getItem('access_token')
  eventSource = new EventSource(`/api/analysis/stream?access_token=${token}`)

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.done) {
      eventSource.close()
      loading.value = false
      return
    }

    // 统计数据（非 LLM 部分）
    if (data.stats) {
      analysis.value = {
        ...analysis.value,
        ...data.stats,
      }
      if (data.stats.dimension_trends && Object.keys(data.stats.dimension_trends).length > 0) {
        nextTick(() => renderChart(data.stats.dimension_trends))
      }
      return
    }

    // LLM 流式内容
    if (data.content) {
      streamingContent.value += data.content
      // 尝试解析已生成的 LLM 内容
      tryParsePartial(streamingContent.value)
    }
  }

  eventSource.onerror = () => {
    eventSource.close()
    loading.value = false
    // 出错时尝试同步加载
    api.get('/api/analysis').then((res) => {
      analysis.value = res.data
      if (res.data.total_interviews > 0 && res.data.dimension_trends) {
        nextTick(() => renderChart(res.data.dimension_trends))
      }
    }).catch(() => {})
  }
})

function tryParsePartial(text) {
  if (!analysis.value) {
    analysis.value = { total_interviews: 0, average_score: 0, dimension_trends: {}, strength: '', weakness: '', development_plan: '' }
  }

  if (!analysis.value.strength) {
    const m = text.match(/"strength"\s*:\s*"((?:[^"\\]|\\.)*)"/)
    if (m) analysis.value.strength = m[1].replace(/\\n/g, '\n').replace(/\\"/g, '"')
  }
  if (!analysis.value.weakness) {
    const m = text.match(/"weakness"\s*:\s*"((?:[^"\\]|\\.)*)"/)
    if (m) analysis.value.weakness = m[1].replace(/\\n/g, '\n').replace(/\\"/g, '"')
  }
  if (!analysis.value.development_plan) {
    const m = text.match(/"development_plan"\s*:\s*"((?:[^"\\]|\\.)*)"/)
    if (m) analysis.value.development_plan = m[1].replace(/\\n/g, '\n').replace(/\\"/g, '"')
  }
}

onUnmounted(() => {
  if (eventSource) eventSource.close()
})

function renderChart(trends) {
  if (!chartRef.value) return

  const chart = echarts.init(chartRef.value)
  const dimensionNames = Object.keys(trends)
  const maxLen = Math.max(...dimensionNames.map((k) => trends[k].length))
  const xAxis = Array.from({ length: maxLen }, (_, i) => `第${i + 1}次`)

  const series = dimensionNames.map((name) => ({
    name,
    type: 'line',
    data: trends[name],
    smooth: true,
  }))

  chart.setOption({
    title: { text: '各维度评分趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { data: dimensionNames, bottom: 0 },
    xAxis: { type: 'category', data: xAxis },
    yAxis: { type: 'value', min: 0, max: 100 },
    series,
  })
}
</script>

<style scoped>
.analysis-container {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header h2 {
  margin: 0;
}

.stats-section {
  display: flex;
  gap: 48px;
  margin-bottom: 24px;
}

.chart-section {
  margin: 24px 0;
}

.summary-section {
  margin: 24px 0;
}

.summary-card h3 {
  margin: 0 0 8px 0;
}

.summary-card p {
  color: #606266;
  line-height: 1.6;
}

.plan-section h3 {
  margin: 0 0 8px 0;
}

.plan-section p {
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
}

.placeholder-text {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-style: italic;
}
</style>
