<template>
  <div class="interview-container">
    <div class="interview-header">
      <h3>AI 面试</h3>
      <el-button type="danger" size="small" @click="handleEnd" :loading="ending">结束面试</el-button>
    </div>

    <!-- 消息列表 -->
    <div class="chat-messages" ref="messagesRef">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message', msg.role === 'user' ? 'message-user' : 'message-ai']"
      >
        <div class="message-role">{{ msg.role === 'user' ? '我' : 'AI 面试官' }}</div>
        <div class="message-content">{{ msg.content }}</div>
      </div>
      <!-- AI 正在回复时显示的加载提示 -->
      <div v-if="aiLoading" class="message message-ai">
        <div class="message-role">AI 面试官</div>
        <div class="message-content">{{ aiStreamingContent || '思考中...' }}</div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input">
      <el-input
        ref="inputRef"
        v-model="inputContent"
        type="textarea"
        placeholder="输入你的回答..."
        @keyup.enter.ctrl="sendMessage"
        :disabled="aiLoading"
      />
      <div class="input-actions">
        <span class="hint">Ctrl + Enter 发送</span>
        <el-button type="primary" @click="sendMessage" :loading="aiLoading" :disabled="!inputContent.trim()">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const route = useRoute()
const router = useRouter()
const sessionId = route.params.id

const messages = ref([])
const inputContent = ref('')
const aiLoading = ref(false)
const aiStreamingContent = ref('')
const ending = ref(false)
const messagesRef = ref(null)
const inputRef = ref(null)

// 输入内容变化时自动撑高 textarea，最多 120px
watch(inputContent, () => {
  const textarea = inputRef.value?.$el?.querySelector('textarea')
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
  }
})

// 滚动到消息底部
function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// 发送用户消息
async function sendMessage() {
  const content = inputContent.value.trim()
  if (!content) return

  // 先在界面上显示用户消息
  messages.value.push({ role: 'user', content })
  inputContent.value = ''
  scrollToBottom()

  // 调后端存消息
  try {
    await api.post(`/api/interview/${sessionId}/message`, { content })
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发送失败')
    return
  }

  // 开始流式接收 AI 回复
  aiLoading.value = true
  aiStreamingContent.value = ''

  const token = localStorage.getItem('access_token')
  const eventSource = new EventSource(
    `/api/interview/${sessionId}/stream?access_token=${token}`
  )

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.done) {
      // 流式结束
      eventSource.close()
      messages.value.push({ role: 'assistant', content: aiStreamingContent.value })
      aiStreamingContent.value = ''
      aiLoading.value = false
      scrollToBottom()
      return
    }

    // 逐字追加显示
    aiStreamingContent.value += data.content
    scrollToBottom()
  }

  eventSource.onerror = () => {
    eventSource.close()
    aiLoading.value = false
    ElMessage.error('AI 回复中断')
  }
}

// 结束面试
async function handleEnd() {
  try {
    await ElMessageBox.confirm('确定要结束本次面试吗？', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  ending.value = true
  try {
    await api.post(`/api/interview/${sessionId}/end`)
    ElMessage.success('面试已结束')
    router.push(`/interview/${sessionId}/result`)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '结束面试失败')
  } finally {
    ending.value = false
  }
}

onMounted(async () => {
  // 加载历史对话记录
  try {
    const response = await api.get(`/api/interview/${sessionId}/detail`)
    messages.value = response.data.conversations.map((c) => ({
      role: c.role,
      content: c.content,
    }))
    scrollToBottom()
  } catch {
    // 加载失败不影响使用
  }
})
</script>

<style scoped>
.interview-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.interview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  border-bottom: 1px solid #e4e7ed;
}

.interview-header h3 {
  margin: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.message {
  margin-bottom: 16px;
  max-width: 70%;
}

.message-user {
  margin-left: auto;
}

.message-ai {
  margin-right: auto;
}

.message-role {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.message-content {
  padding: 10px 14px;
  border-radius: 8px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

.message-user .message-content {
  background: #409eff;
  color: white;
}

.message-ai .message-content {
  background: #f4f4f5;
  color: #303133;
}

.chat-input {
  padding: 16px 24px;
  border-top: 1px solid #e4e7ed;
}

.chat-input :deep(textarea) {
  resize: none;
  min-height: 40px;
  max-height: 120px;
  overflow-y: auto;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.hint {
  font-size: 12px;
  color: #909399;
}
</style>
