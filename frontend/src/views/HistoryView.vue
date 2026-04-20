<template>
  <div class="history-container">
    <el-card>
      <div class="header">
        <h2>面试历史</h2>
        <el-button @click="$router.push('/')" size="small">返回首页</el-button>
      </div>

      <!-- 筛选 -->
      <div class="filters">
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable @change="loadList" style="width: 120px">
          <el-option label="进行中" value="进行中" />
          <el-option label="已完成" value="已完成" />
        </el-select>
        <el-input v-model="positionFilter" placeholder="岗位筛选" clearable @input="debounceLoad" style="width: 200px; margin-left: 8px" />
      </div>

      <!-- 列表 -->
      <el-table :data="sessions" v-loading="loading" style="margin-top: 16px">
        <el-table-column prop="position" label="岗位" width="120" />
        <el-table-column prop="style" label="风格" width="100" />
        <el-table-column prop="difficulty" label="难度" width="80" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === '已完成' ? 'success' : 'warning'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="viewDetail(row.id)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadList"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

const router = useRouter()
const sessions = ref([])
const loading = ref(false)
const statusFilter = ref('')
const positionFilter = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)
let debounceTimer = null

onMounted(() => {
  loadList()
})

async function loadList() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (statusFilter.value) params.status = statusFilter.value
    if (positionFilter.value) params.position = positionFilter.value

    const response = await api.get('/api/interview/list', { params })
    sessions.value = response.data
    total.value = response.data.length < pageSize ? (page.value - 1) * pageSize + response.data.length : page.value * pageSize + 1
  } catch {
    ElMessage.error('加载历史记录失败')
  } finally {
    loading.value = false
  }
}

function debounceLoad() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    loadList()
  }, 300)
}

function viewDetail(sessionId) {
  router.push(`/interview/${sessionId}/result`)
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.history-container {
  padding: 24px;
  max-width: 900px;
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

.filters {
  display: flex;
  align-items: center;
}

.pagination {
  margin-top: 16px;
  text-align: center;
}
</style>
