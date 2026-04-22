<template>
  <div class="analysis-container">
    <el-card>
      <div class="header">
        <h2>个人能力分析</h2>
        <el-button @click="$router.push('/')" size="small">返回首页</el-button>
      </div>

      <div v-if="loading" v-loading="true" style="min-height: 200px" />

      <template v-else-if="analysis">
        <!-- 基础统计 -->
        <div class="stats-section">
          <el-statistic title="面试次数" :value="analysis.total_interviews" />
          <el-statistic title="平均分" :value="analysis.average_score" :precision="1" />
        </div>

        <!-- 无数据提示 -->
        <el-empty v-if="analysis.total_interviews === 0" description="暂无面试记录，请先完成面试" />

        <template v-else>
          <!-- 能力趋势折线图 -->
          <div class="chart-section">
            <h3>能力趋势</h3>
            <div ref="chartRef" style="width: 100%; height: 350px"></div>
          </div>

          <el-divider />

          <!-- 优势与不足 -->
          <div class="summary-section">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-card shadow="never" class="summary-card strength">
                  <h3>优势</h3>
                  <p>{{ analysis.strength }}</p>
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card shadow="never" class="summary-card weakness">
                  <h3>不足</h3>
                  <p>{{ analysis.weakness }}</p>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <el-divider />

          <!-- 发展建议 -->
          <div class="plan-section">
            <h3>发展建议</h3>
            <p>{{ analysis.development_plan }}</p>
          </div>
        </template>
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import api from '../api'

const analysis = ref(null)
const loading = ref(true)
const chartRef = ref(null)

onMounted(async () => {
  try {
    const response = await api.get('/api/analysis')
    analysis.value = response.data

    if (response.data.total_interviews > 0) {
      await nextTick()
      renderChart(response.data.dimension_trends)
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '加载分析失败')
  } finally {
    loading.value = false
  }
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
</style>
