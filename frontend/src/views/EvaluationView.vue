<template>
  <div class="evaluation-container">
    <el-card v-if="loading" v-loading="true" style="min-height: 200px" />
    <template v-else-if="detail">
      <!-- 会话信息 -->
      <el-card class="session-card">
        <h2>面试评价</h2>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="岗位">{{ detail.session.position }}</el-descriptions-item>
          <el-descriptions-item label="风格">{{ detail.session.style }}</el-descriptions-item>
          <el-descriptions-item label="难度">{{ detail.session.difficulty }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ detail.session.status }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 评价内容 -->
      <el-card v-if="detail.evaluation" class="eval-card">
        <div class="score-section">
          <div class="overall-score">
            <span class="score-number">{{ detail.evaluation.overall_score }}</span>
            <span class="score-label">总体评分</span>
          </div>
        </div>

        <div class="chart-section">
          <div ref="chartRef" style="width: 400px; height: 300px; margin: 0 auto"></div>
        </div>

        <el-divider />

        <h3>总体评价</h3>
        <p>{{ detail.evaluation.summary }}</p>

        <el-divider />

        <h3>改进建议</h3>
        <p>{{ detail.evaluation.suggestions }}</p>

        <el-divider />

        <h3>待改进问答</h3>
        <el-timeline v-if="detail.evaluation.improvements.length > 0">
          <el-timeline-item
            v-for="(item, index) in detail.evaluation.improvements"
            :key="index"
            :timestamp="'改进点 ' + (index + 1)"
          >
            {{ item }}
          </el-timeline-item>
        </el-timeline>
        <p v-else>暂无需要改进的地方</p>
      </el-card>

      <el-card v-else class="eval-card">
        <el-empty description="暂无评价信息" />
      </el-card>

      <div class="actions">
        <el-button @click="$router.push('/')">返回首页</el-button>
        <el-button type="primary" @click="$router.push('/history')">查看历史记录</el-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import api from '../api'

const route = useRoute()
const detail = ref(null)
const loading = ref(true)
const chartRef = ref(null)

onMounted(async () => {
  const sessionId = route.params.id
  try {
    const response = await api.get(`/api/interview/${sessionId}/detail`)
    detail.value = response.data

    // 如果有评价，渲染雷达图
    if (detail.value.evaluation) {
      await nextTick()
      renderChart(detail.value.evaluation.dimensions)
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取评价失败')
  } finally {
    loading.value = false
  }
})

function renderChart(dimensions) {
  if (!chartRef.value) return

  const chart = echarts.init(chartRef.value)
  const labels = Object.keys(dimensions)
  const values = Object.values(dimensions)

  chart.setOption({
    title: { text: '维度评分', left: 'center' },
    radar: {
      indicator: labels.map((label) => ({ name: label, max: 100 })),
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

.actions {
  text-align: center;
  margin-top: 16px;
}
</style>
