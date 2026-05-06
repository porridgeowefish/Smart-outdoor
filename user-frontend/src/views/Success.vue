<template>
  <div class="flex flex-col h-full grow bg-slate-50 relative overflow-hidden">
    <div class="h-[220px] bg-emerald-500 absolute top-0 w-full rounded-b-[40px]"></div>

    <div class="flex flex-col h-full z-10 pt-16 px-6 pb-6">
      <div class="flex justify-between items-center mb-8">
        <h1 class="text-[26px] font-bold text-white tracking-[-0.5px]">个人主页</h1>
        <button
          @click="logout"
          class="text-white bg-white/20 px-4 py-2 rounded-xl text-[14px] font-medium hover:bg-white/30 transition-colors border-none cursor-pointer"
        >
          退出
        </button>
      </div>

      <div class="bg-white rounded-[32px] p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 flex-grow flex flex-col relative overflow-hidden">
        <div v-if="loading" class="absolute inset-0 bg-white/90 flex flex-col items-center justify-center z-10">
          <span class="animate-spin w-8 h-8 border-[3px] border-slate-200 border-t-emerald-500 rounded-full mb-4"></span>
          <span class="text-slate-500 text-[14px]">加载中...</span>
        </div>

        <div v-if="user" class="flex flex-col flex-grow">
          <div class="flex flex-col items-center mb-8 mt-2">
            <label class="relative cursor-pointer group">
              <div class="w-[88px] h-[88px] bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center text-[36px] font-bold mb-4 overflow-hidden border-4 border-white shadow-sm">
                <img v-if="user.avatar_url" :src="user.avatar_url" alt="avatar" class="w-full h-full object-cover" />
                <span v-else>{{ avatarInitial }}</span>
              </div>
              <span class="absolute bottom-3 right-0 bg-slate-900 text-white text-[11px] px-2 py-1 rounded-lg shadow-sm group-hover:bg-emerald-600 transition-colors">
                上传
              </span>
              <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" class="hidden" @change="uploadAvatar" />
            </label>

            <h2 class="text-[22px] font-bold text-slate-800 tracking-[-0.5px] leading-tight">{{ user.nickname }}</h2>
            <p class="text-slate-500 text-[15px] mt-1">@{{ user.username }}</p>
            <div class="mt-3 px-3 py-1 bg-emerald-50 text-emerald-600 rounded-lg text-[12px] font-bold uppercase tracking-[1px]">
              {{ user.role || 'User' }}
            </div>
            <p v-if="avatarUploading" class="text-emerald-600 text-[13px] mt-3">头像上传中...</p>
          </div>

          <form v-if="editing" @submit.prevent="updateProfile" class="flex flex-col flex-grow">
            <div class="mb-5 flex flex-col">
              <label for="nickname" class="text-[13px] font-semibold text-slate-500 mb-2 uppercase tracking-[0.5px]">修改昵称</label>
              <input
                id="nickname"
                v-model="editForm.nickname"
                type="text"
                placeholder="设置新昵称"
                class="w-full px-4 py-[14px] bg-slate-50 border border-slate-200 rounded-xl outline-none focus:border-emerald-500 transition-colors text-base text-slate-800 placeholder:text-slate-400"
              />
            </div>

            <div v-if="error" class="p-3 bg-red-50 text-red-600 text-[14px] rounded-xl mb-4 border border-red-100 leading-tight">
              {{ error }}
            </div>

            <div class="mt-auto flex gap-3 pt-4">
              <button
                type="button"
                @click="editing = false"
                class="flex-1 p-[14px] bg-slate-100 text-slate-600 font-semibold rounded-xl hover:bg-slate-200 transition-colors text-[15px] border-none cursor-pointer"
              >
                取消
              </button>
              <button
                type="submit"
                :disabled="updating"
                class="flex-[2] p-[14px] bg-emerald-500 text-white font-semibold rounded-xl hover:bg-emerald-600 transition-colors disabled:opacity-70 flex items-center justify-center gap-2 text-[15px] border-none cursor-pointer"
              >
                <span v-if="updating" class="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full"></span>
                {{ updating ? '保存中...' : '保存更改' }}
              </button>
            </div>
          </form>

          <div v-else class="flex flex-col flex-grow">
            <div class="flex flex-col space-y-0 mb-8 border border-slate-100 rounded-2xl overflow-hidden bg-white">
              <div class="flex justify-between items-center py-[14px] px-4 border-b border-slate-100 last:border-b-0">
                <span class="text-slate-500 text-[14px] font-medium">账号状态</span>
                <span class="text-slate-800 text-[14px] font-semibold">{{ user.status === 'active' ? '正常' : (user.status || '未知') }}</span>
              </div>
              <div class="flex justify-between items-center py-[14px] px-4 border-b border-slate-100 last:border-b-0">
                <span class="text-slate-500 text-[14px] font-medium">注册时间</span>
                <span class="text-slate-800 text-[14px] font-semibold">{{ formatDate(user.created_at) }}</span>
              </div>
            </div>

            <div v-if="error" class="p-3 bg-red-50 text-red-600 text-[14px] rounded-xl mb-4 border border-red-100 leading-tight">
              {{ error }}
            </div>

            <div class="mt-auto">
              <button
                @click="startEdit"
                class="w-full p-[14px] bg-emerald-50 text-emerald-600 font-semibold rounded-xl hover:bg-emerald-100 transition-colors flex items-center justify-center text-[15px] border-none cursor-pointer"
              >
                编辑个人资料
              </button>
            </div>
          </div>
        </div>

        <div v-else-if="!loading" class="flex flex-col items-center justify-center h-full text-center">
          <p class="text-slate-500 mb-6 text-[15px] max-w-[200px] leading-relaxed">未能加载用户信息，请重新登录</p>
          <button @click="logout" class="px-6 py-[12px] bg-slate-800 text-white rounded-xl text-[15px] font-medium border-none cursor-pointer hover:bg-slate-700 w-full sm:w-auto">重新登录</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(true)
const updating = ref(false)
const avatarUploading = ref(false)
const error = ref('')
const user = ref<any>(null)
const editing = ref(false)

const editForm = reactive({
  nickname: '',
})

const avatarInitial = computed(() => {
  const source = user.value?.nickname || user.value?.username || '?'
  return source.charAt(0).toUpperCase()
})

onMounted(async () => {
  await fetchProfile()
})

const authHeaders = () => {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : null
}

const fetchProfile = async () => {
  const headers = authHeaders()
  if (!headers) {
    loading.value = false
    router.replace('/login')
    return
  }

  try {
    const res = await fetch('/api/me', { headers })

    if (res.status === 401) {
      logout()
      return
    }

    if (!res.ok) {
      throw new Error(`获取用户信息失败 (${res.status})`)
    }

    user.value = await res.json()
  } catch (err: any) {
    error.value = err.message || '网络错误'
  } finally {
    loading.value = false
  }
}

const uploadAvatar = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  const headers = authHeaders()
  if (!headers) {
    router.replace('/login')
    return
  }

  avatarUploading.value = true
  error.value = ''

  try {
    const formData = new FormData()
    formData.append('file', file)

    const res = await fetch('/api/me/avatar', {
      method: 'POST',
      headers,
      body: formData,
    })

    if (!res.ok) {
      const data = await res.json().catch(() => null)
      throw new Error(data?.message || `头像上传失败 (${res.status})`)
    }

    user.value = await res.json()
  } catch (err: any) {
    error.value = err.message || '头像上传失败'
  } finally {
    avatarUploading.value = false
    input.value = ''
  }
}

const startEdit = () => {
  editForm.nickname = user.value?.nickname || ''
  editing.value = true
  error.value = ''
}

const updateProfile = async () => {
  updating.value = true
  error.value = ''
  const headers = authHeaders()
  if (!headers) {
    router.replace('/login')
    return
  }

  try {
    const payload: { nickname?: string } = {}
    if (editForm.nickname !== user.value?.nickname) {
      payload.nickname = editForm.nickname.trim()
    }

    if (Object.keys(payload).length === 0) {
      editing.value = false
      return
    }

    const res = await fetch('/api/me', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: JSON.stringify(payload),
    })

    if (!res.ok) {
      const data = await res.json().catch(() => null)
      throw new Error(data?.message || `保存失败 (${res.status})`)
    }

    user.value = await res.json()
    editing.value = false
  } catch (err: any) {
    error.value = err.message || '网络错误'
  } finally {
    updating.value = false
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('token_type')
  router.replace('/login')
}
</script>
