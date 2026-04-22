import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',  // 监听所有网卡，局域网内其他主机可访问
    // 前端开发代理：把 /api 开头的请求转发到后端 9000 端口
    proxy: {
      '/api': {
        target: 'http://10.189.139.64:9000',
        changeOrigin: true,
      },
    },
  },
})
