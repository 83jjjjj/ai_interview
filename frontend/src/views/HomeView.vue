<template>
  <div class="home">
    <nav class="nav">
      <h1>AI 面试器</h1>
      <div class="nav-links">
        <router-link to="/">首页</router-link>
        <router-link to="/history">历史</router-link>
        <router-link to="/analysis">能力分析</router-link>
        <a href="#" @click.prevent="handleLogout">退出</a>
      </div>
    </nav>

    <section class="hero">
      <h2>准备好了吗，{{ user?.username }}？</h2>
      <p>上传简历，选择岗位和面试风格，开始一场 AI 模拟面试。</p>
      <div class="hero-actions">
        <el-button type="primary" @click="$router.push('/resume')">上传简历</el-button>
        <el-button @click="$router.push('/interview/config')">发起面试</el-button>
      </div>
    </section>

    <section class="features">
      <div class="feature-card">
        <h3>AI 面试</h3>
        <p>基于简历和岗位，AI 面试官实时提问，支持追问和话题切换</p>
      </div>
      <div class="feature-card">
        <h3>智能评价</h3>
        <p>面试结束自动生成多维度评分和改进建议</p>
      </div>
      <div class="feature-card">
        <h3>能力追踪</h3>
        <p>多次面试后，AI 分析你的能力趋势和发展方向</p>
      </div>
    </section>
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
.nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 48px;
  border-bottom: 1px solid #eee;
}

.nav h1 {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.5px;
  margin: 0;
}

.nav-links {
  display: flex;
  gap: 32px;
}

.nav-links a {
  color: #666;
  text-decoration: none;
  font-size: 14px;
}

.nav-links a:hover {
  color: #1a1a1a;
}

.hero {
  padding: 80px 48px;
  max-width: 600px;
}

.hero h2 {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 12px;
}

.hero p {
  color: #666;
  font-size: 16px;
  line-height: 1.6;
  margin-bottom: 32px;
}

.hero-actions {
  display: flex;
  gap: 12px;
}

.features {
  display: flex;
  gap: 24px;
  padding: 0 48px 80px;
}

.feature-card {
  flex: 1;
  padding: 24px;
  border: 1px solid #eee;
  border-radius: 8px;
}

.feature-card h3 {
  font-size: 16px;
  margin-bottom: 8px;
}

.feature-card p {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
}
</style>
