<template>
  <div class="resume-container">
    <!-- 上传区域 -->
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <h3>上传简历</h3>
          <router-link to="/">返回首页</router-link>
        </div>
      </template>

      <el-upload
        class="upload-area"
        drag
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="fileList"
        accept=".pdf,.png,.jpg,.jpeg"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">拖拽文件到这里，或<em>点击选择</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 PDF、PNG、JPG 格式</div>
        </template>
      </el-upload>

      <el-button
        type="primary"
        @click="handleUpload"
        :loading="uploading"
        :disabled="!selectedFile"
        style="width: 100%; margin-top: 16px"
      >
        上传并解析
      </el-button>
    </el-card>

    <!-- 简历列表 -->
    <el-card class="list-card">
      <template #header>
        <h3>我的简历</h3>
      </template>

      <el-table :data="resumes" v-loading="loading" empty-text="暂无简历">
        <el-table-column prop="filename" label="文件名" />
        <el-table-column label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="showParsed(row)">查看解析</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 解析结果对话框 -->
    <el-dialog v-model="dialogVisible" title="AI 解析结果" width="600px">
      <div v-if="parsedInfo" class="parsed-content">
        <p><strong>姓名：</strong>{{ parsedInfo.name }}</p>
        <p><strong>邮箱：</strong>{{ parsedInfo.email }}</p>
        <p><strong>电话：</strong>{{ parsedInfo.phone }}</p>

        <h4 v-if="parsedInfo.education.length">教育背景</h4>
        <div v-for="(edu, i) in parsedInfo.education" :key="i" class="parsed-item">
          <p>{{ edu.school }} - {{ edu.degree }} {{ edu.major }} ({{ edu.duration }})</p>
        </div>

        <h4 v-if="parsedInfo.work_experience.length">工作经历</h4>
        <div v-for="(work, i) in parsedInfo.work_experience" :key="i" class="parsed-item">
          <p><strong>{{ work.company }}</strong> - {{ work.position }} ({{ work.duration }})</p>
          <p>{{ work.responsibilities }}</p>
        </div>

        <h4 v-if="parsedInfo.skills.length">技能</h4>
        <el-tag v-for="skill in parsedInfo.skills" :key="skill" style="margin: 4px">
          {{ skill }}
        </el-tag>

        <h4 v-if="parsedInfo.summary">总结</h4>
        <p>{{ parsedInfo.summary }}</p>
      </div>
      <div v-else>解析结果为空</div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '../api'

const resumes = ref([])
const loading = ref(false)
const uploading = ref(false)
const selectedFile = ref(null)
const fileList = ref([])
const dialogVisible = ref(false)
const parsedInfo = ref(null)

onMounted(() => {
  fetchResumes()
})

async function fetchResumes() {
  loading.value = true
  try {
    const response = await api.get('/api/resume/list')
    resumes.value = response.data
  } catch {
    ElMessage.error('获取简历列表失败')
  } finally {
    loading.value = false
  }
}

function handleFileChange(file) {
  selectedFile.value = file.raw
}

async function handleUpload() {
  if (!selectedFile.value) return

  uploading.value = true
  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    await api.post('/api/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success('上传成功，AI 正在解析')
    selectedFile.value = null
    fileList.value = []
    fetchResumes()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

function showParsed(row) {
  try {
    parsedInfo.value = row.parsed_content ? JSON.parse(row.parsed_content) : null
  } catch {
    parsedInfo.value = null
  }
  dialogVisible.value = true
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.resume-container {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.parsed-content h4 {
  margin-top: 16px;
  margin-bottom: 8px;
  color: #303133;
}

.parsed-item {
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}
</style>
