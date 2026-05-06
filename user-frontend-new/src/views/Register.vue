<template>
  <div class="flex flex-col h-full grow px-7 bg-slate-50 relative overflow-hidden">
    <div v-if="success" class="absolute inset-0 bg-slate-50 flex flex-col items-center justify-center z-50 text-center p-10">
      <div class="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-[40px] mb-6 font-bold">
        ✓
      </div>
      <h2 class="text-[24px] font-bold text-slate-800 mb-3">注册成功</h2>
      <p class="text-slate-500 text-[15px] leading-[1.5]">账号已创建，正在跳转到登录页。</p>
    </div>

    <div v-else class="flex flex-col h-full grow">
      <div class="mt-12 mb-12 flex flex-col">
        <div class="w-12 h-12 bg-emerald-500 text-white rounded-xl flex items-center justify-center mb-6">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 20L12 4L21 20H3Z"/></svg>
        </div>
        <h1 class="text-[28px] font-bold text-slate-800 mb-2 leading-tight">加入山野</h1>
        <p class="text-[15px] text-slate-500">用最简单的账号开始上传线路</p>
      </div>

      <form @submit.prevent="handleRegister" class="flex flex-col flex-grow pb-8">
        <div class="mb-5 flex flex-col">
          <label for="nickname" class="text-[13px] font-semibold text-slate-500 mb-2 uppercase tracking-[0.5px]">昵称</label>
          <input
            id="nickname"
            v-model.trim="form.nickname"
            type="text"
            placeholder="山野用户"
            class="w-full px-4 py-[14px] bg-white border border-slate-200 rounded-xl outline-none focus:border-emerald-500 transition-colors text-base text-slate-800 placeholder:text-slate-400"
          />
        </div>

        <div class="mb-5 flex flex-col">
          <label for="username" class="text-[13px] font-semibold text-slate-500 mb-2 uppercase tracking-[0.5px]">用户名</label>
          <input
            id="username"
            v-model.trim="form.username"
            type="text"
            required
            autocomplete="username"
            placeholder="outdoor_user"
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
            autocomplete="new-password"
            placeholder="plain_password"
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
            {{ loading ? '提交中...' : '立即注册' }}
          </button>

          <button type="button" @click="$router.push('/login')" class="w-full mt-4 bg-transparent text-emerald-500 text-[14px] font-normal border-none cursor-pointer hover:opacity-80 transition-opacity">
            已有账号？登录
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '../api'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const success = ref(false)

const form = reactive({
  username: '',
  password: '',
  nickname: '',
})

const handleRegister = async () => {
  loading.value = true
  error.value = ''

  try {
    await register({
      username: form.username,
      password: form.password,
      nickname: form.nickname || undefined,
    })
    success.value = true
    window.setTimeout(() => {
      router.replace({ path: '/login', query: { username: form.username } })
    }, 900)
  } catch (e: any) {
    error.value = e.message || '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>
