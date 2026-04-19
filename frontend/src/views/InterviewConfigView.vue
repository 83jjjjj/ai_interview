<template>
  <div class="config-container">
    <el-card class="config-card">
      <h2>发起面试</h2>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="选择简历" prop="resume_id">
          <el-select v-model="form.resume_id" placeholder="请选择简历" style="width: 100%">
            <el-option
              v-for="item in resumes"
              :key="item.id"
              :label="item.filename"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="面试岗位" prop="position">
          <el-input v-model="form.position" placeholder="如：后端开发" />
        </el-form-item>
        <el-form-item label="面试风格">
          <el-select v-model="form.style" style="width: 100%">
            <el-option label="综合面试" value="综合面试" />
            <el-option label="深度追问" value="深度追问" />
            <el-option label="逻辑考察" value="逻辑考察" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="form.difficulty" style="width: 100%">
            <el-option label="简单" value="简单" />
            <el-option label="中等" value="中等" />
            <el-option label="困难" value="困难" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleStart" :loading="loading">开始面试</el-button>
          <el-button @click="$router.push('/')">返回</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const resumes = ref([])

const form = reactive({
  resume_id: null,
  position: '',
  style: '综合面试',
  difficulty: '中等',
})

const rules = {
  resume_id: [{ required: true, message: '请选择简历', trigger: 'change' }],
  position: [{ required: true, message: '请输入面试岗位', trigger: 'blur' }],
}

onMounted(async () => {
  try {
    const response = await api.get('/api/resume/list')
    resumes.value = response.data
  } catch {
    ElMessage.error('获取简历列表失败')
  }
})

async function handleStart() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const response = await api.post('/api/interview/start', form)
    router.push(`/interview/${response.data.id}`)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '创建面试失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.config-container {
  padding: 24px;
  max-width: 600px;
  margin: 0 auto;
}

.config-card h2 {
  margin-bottom: 24px;
}
</style>
