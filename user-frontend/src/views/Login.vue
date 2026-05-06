<template>
  <div class="flex flex-col h-full grow px-7 py-0 bg-slate-50 relative">
    <div class="mt-10 mb-12 flex flex-col pt-2">
      <div class="w-12 h-12 bg-emerald-500 text-white rounded-xl flex items-center justify-center mb-6">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M3 20L12 4L21 20H3Z"/></svg>
      </div>
      <h1 class="text-[28px] font-bold text-slate-800 tracking-[-0.5px] mb-2 leading-tight">欢迎回来</h1>
      <p class="text-[15px] text-slate-500">登录以继续探索</p>
    </div>

    <form @submit.prevent="handleLogin" class="flex flex-col flex-grow">
      <div class="mb-5 flex flex-col">
        <label for="username" class="text-[13px] font-semibold text-slate-500 mb-2 uppercase tracking-[0.5px]">用户名</label>
        <input 
          id="username" 
          v-model="form.username" 
          type="text" 
          required
          placeholder="输入用户名"
          class="w-full px-4 py-[14px] bg-white border border-slate-200 rounded-xl outline-none focus:border-emerald-500 transition-colors text-base text-slate-800 placeholder:text-slate-400"
        />
      </div>
      
      <div class="mb-5 flex flex-col">
        <label for="password" class="text-[13px] font-semibold text-slate-500 mb-2 uppercase tracking-[0.5px]">密码</label>
        <input 
          id="password" 
          v-model="form.password" 
          type="password" 
          required
          placeholder="输入密码"
          class="w-full px-4 py-[14px] bg-white border border-slate-200 rounded-xl outline-none focus:border-emerald-500 transition-colors text-base text-slate-800 placeholder:text-slate-400"
        />
      </div>

      <div v-if="error" class="p-3 bg-red-50 text-red-600 text-[14px] rounded-xl mb-4 border border-red-100">
        {{ error }}
      </div>

      <div class="mt-3 flex flex-col">
        <button 
          type="submit" 
          :disabled="loading"
          class="w-full p-4 bg-emerald-500 text-white font-semibold rounded-xl hover:bg-emerald-600 transition-colors disabled:opacity-70 flex items-center justify-center gap-2 text-[16px] border-none cursor-pointer"
        >
          <span v-if="loading" class="animate-spin w-5 h-5 border-2 border-white/30 border-t-white rounded-full"></span>
          {{ loading ? '登录中...' : '登录' }}
        </button>
        
        <button type="button" @click="$router.push('/register')" class="w-full mt-4 bg-transparent text-emerald-500 text-[14px] font-normal border-none cursor-pointer hover:opacity-80 transition-opacity">
          没有账号？注册
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const error = ref('')

const form = reactive({
  username: '',
  password: ''
})

onMounted(() => {
  if (route.query.username) {
    form.username = route.query.username as string
  }
})

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(form)
    })
    
    if (!response.ok) {
      let errorMsg = '登录请求失败'
      try {
        const errorData = await response.json()
        if (errorData.detail) {
          errorMsg = Array.isArray(errorData.detail) 
            ? errorData.detail.map((err: any) => err.msg).join(', ') 
            : errorData.detail
        }
      } catch (e) {}

      if (response.status === 404) {
         errorMsg = '登录接口未找到 (404)'
      }
      throw new Error(errorMsg)
    } else {
      const data = await response.json()
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('token_type', data.token_type || 'Bearer')
      }
      
      router.push('/success')
    }
  } catch (e: any) {
    console.error('Login error:', e)
    error.value = e.message || '网络请求错误，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>
