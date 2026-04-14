<template>
  <div class="home-container">
    <el-card>
      <h2>欢迎，{{ user?.username }}</h2>
      <p>AI 面试器 - 首页</p>
      <div style="margin-top: 16px">
        <el-button type="primary" @click="$router.push('/resume')">上传简历</el-button>
        <el-button @click="handleLogout">退出登录</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const user = ref(null)

onMounted(async () => {
  try {
    const response = await api.get('/api/me')
    user.value = response.data
  } catch {
    router.push('/login')
  }
})

function handleLogout() {
  localStorage.removeItem('access_token')
  router.push('/login')
}
</script>

<style scoped>
.home-container {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}
</style>
