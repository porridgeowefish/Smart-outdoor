<template>
  <div class="flex flex-col h-full bg-slate-50 relative">
    <div class="h-[44px] bg-white border-b border-slate-100 flex items-center justify-between px-4 shrink-0 shadow-[0_2px_4px_rgba(0,0,0,0.02)] z-10 sticky top-0">
      <div class="flex items-center gap-3">
        <h1 class="text-[18px] font-bold text-slate-800">线路</h1>
        <div class="flex items-center gap-1 text-[14px] text-slate-600 font-medium">
          真实数据
        </div>
      </div>
      <button @click="triggerRouteUpload" :disabled="isUploading" class="text-emerald-500 bg-emerald-50/50 px-3 py-1.5 rounded-full text-[12px] font-bold flex items-center gap-1 hover:bg-emerald-100 transition-colors">
        <span v-if="isUploading" class="animate-spin w-3 h-3 border-2 border-emerald-200 border-t-emerald-500 rounded-full"></span>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>
        {{ isUploading ? '上传中...' : '发布线路' }}
      </button>
      <input type="file" ref="routeInput" class="hidden" accept=".kml,.gpx,.geojson,.json" @change="onRouteSelected" />
      <input type="file" ref="coverInput" class="hidden" accept="image/jpeg,image/png,image/webp" @change="onCoverSelected" />
    </div>

    <div class="px-3 pt-3 pb-2 bg-white shrink-0 z-10 sticky top-[44px]">
      <div class="flex gap-2 mb-3">
        <div class="relative flex-grow">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          <input v-model.trim="keyword" @keyup.enter="loadRoutes" type="text" placeholder="搜索线路名称" class="w-full bg-slate-50 border border-transparent rounded-full py-[8px] pl-9 pr-4 text-[13px] outline-none focus:border-emerald-500 focus:bg-white transition-colors placeholder:text-slate-400" />
        </div>
        <button @click="clearKeyword" class="text-slate-400 shrink-0 flex items-center justify-center px-1">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
      </div>

      <div class="flex gap-2 overflow-x-auto hide-scrollbar pb-1 text-[13px]">
        <button @click="visibility = 'all'; loadRoutes()" :class="filterClass('all')" class="shrink-0 px-3 py-1.5 font-medium rounded-full border">全部</button>
        <button @click="visibility = 'public'; loadRoutes()" :class="filterClass('public')" class="shrink-0 px-3 py-1.5 font-medium rounded-full border">公开</button>
        <button @click="visibility = 'private'; loadRoutes()" :class="filterClass('private')" class="shrink-0 px-3 py-1.5 font-medium rounded-full border">我的私有</button>
      </div>
    </div>

    <div class="flex-grow overflow-y-auto px-3 py-3 h-full bg-slate-50">
      <div v-if="isLoading" class="py-16 flex justify-center">
        <span class="animate-spin w-6 h-6 border-2 border-emerald-100 border-t-emerald-500 rounded-full"></span>
      </div>

      <div v-else-if="error" class="bg-red-50 text-red-600 border border-red-100 rounded-xl p-4 text-[13px]">
        {{ error }}
      </div>

      <div v-else-if="routes.length === 0" class="text-center py-16 px-8">
        <div class="w-14 h-14 bg-emerald-50 rounded-2xl mx-auto mb-4 flex items-center justify-center text-emerald-500">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3V6Z"/><path d="M9 3v15"/><path d="M15 6v15"/></svg>
        </div>
        <h3 class="text-[16px] font-bold text-slate-800 mb-1">还没有线路</h3>
        <p class="text-[13px] text-slate-500">上传 KML、GPX 或 GeoJSON 后，这里会显示数据库里的真实线路。</p>
      </div>

      <div v-else>
        <div v-for="route in routes" :key="route.route_id" @click="$router.push(`/routes/${route.route_id}`)" class="bg-white rounded-[16px] p-3 mb-3 flex gap-3 shadow-[0_2px_8px_rgba(0,0,0,0.04)] active:scale-[0.98] transition-transform cursor-pointer">
          <div class="w-[105px] h-[105px] rounded-xl overflow-hidden relative shrink-0 bg-slate-100">
            <img :src="route.cover_image_url || fallbackImage" class="w-full h-full object-cover" />
            <div :class="difficultyColor(route)" class="absolute top-0 left-0 text-slate-800 text-[10px] px-1.5 py-0.5 rounded-br-lg font-bold tracking-wide z-10 opacity-90">
              {{ difficultyLabel(route) }}
            </div>
          </div>

          <div class="flex flex-col flex-grow min-w-0 justify-between py-0.5">
            <div>
              <h3 class="font-bold text-slate-800 text-[15px] mb-1.5 leading-snug line-clamp-2 pr-1">{{ route.name }}</h3>
              <p v-if="route.location" class="text-[11px] text-slate-400 mb-1.5 flex items-center gap-0.5">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                {{ route.location }}
              </p>
              <div class="flex flex-wrap items-center gap-x-2.5 gap-y-1 text-[11px] text-slate-500 mb-2 font-medium">
                <span class="flex items-center gap-0.5 shrink-0">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h5l2.5-4 4.5 8 2.5-4h3"/></svg>
                  {{ formatKm(route.distance_km) }} 公里
                </span>
                <span class="flex items-center gap-0.5 shrink-0">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                  {{ Math.round(route.elevation_gain_m) }} 米爬升
                </span>
                <span class="flex items-center gap-0.5 shrink-0">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  {{ estimateDuration(route) }}
                </span>
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-1.5 mt-auto">
              <span v-for="tag in route.display_tags" :key="tag" class="bg-slate-100 text-slate-600 text-[10px] px-1.5 py-0.5 rounded font-medium">{{ tag }}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded font-medium ml-auto" :class="route.visibility === 'public' ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-500'">
                {{ route.visibility === 'public' ? '公开' : '私有' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="h-4"></div>
    </div>

    <div v-if="showPublishModal" class="absolute inset-0 z-50 bg-white flex flex-col font-sans">
      <div class="h-14 flex items-center justify-between px-4 border-b border-slate-100 shrink-0">
        <button @click="closeUploadModal" class="text-slate-500 font-medium">取消</button>
        <h2 class="text-[16px] font-bold text-slate-800">编辑线路</h2>
        <button @click="submitRoute" :disabled="isSubmitting || !draftRoute.name.trim()" class="text-emerald-500 font-bold disabled:opacity-50">
          {{ isSubmitting ? '保存中...' : '发布' }}
        </button>
      </div>

      <div class="flex-grow overflow-y-auto">
        <div class="relative bg-slate-900 h-[220px]">
          <img :src="coverPreviewUrl || fallbackImage" class="w-full h-full object-cover opacity-70 mix-blend-overlay filter contrast-125" />
          <svg v-if="!coverPreviewUrl" class="absolute inset-0 w-full h-full pointer-events-none drop-shadow-lg" viewBox="0 0 400 220" preserveAspectRatio="none">
            <path d="M 50,150 C 100,100 120,180 200,100 S 280,50 350,80" fill="none" stroke="#10b981" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
            <circle cx="50" cy="150" r="5" fill="#3b82f6" stroke="#ffffff" stroke-width="2" />
            <circle cx="350" cy="80" r="5" fill="#ef4444" stroke="#ffffff" stroke-width="2" />
          </svg>
          <div class="absolute top-3 right-3 flex gap-2">
            <button @click="triggerCoverUpload" class="bg-white/90 text-slate-700 text-[12px] font-bold px-3 py-1.5 rounded-full shadow">
              {{ coverImage ? '更换封面' : '选择封面' }}
            </button>
            <button v-if="coverImage" @click="clearCover" class="bg-black/45 text-white text-[12px] font-bold px-3 py-1.5 rounded-full shadow">
              清除
            </button>
          </div>
          <div class="absolute bottom-0 inset-x-0 bg-gradient-to-t from-slate-900 to-transparent pt-12 pb-3 px-4 text-white">
            <div class="text-[11px] text-white/70 font-bold uppercase tracking-wider mb-1">待上传文件</div>
            <div class="text-[18px] font-bold leading-tight truncate">{{ selectedFile?.name }}</div>
            <div class="text-[12px] text-white/70 mt-1">{{ selectedFile ? formatFileSize(selectedFile.size) : '' }}</div>
          </div>
        </div>

        <div class="p-5">
          <div class="mb-5">
            <label class="block text-[13px] font-bold text-slate-800 mb-2">线路名称 <span class="text-red-500">*</span></label>
            <input v-model="draftRoute.name" type="text" placeholder="给线路起一个名字" class="w-full bg-slate-50 border border-slate-200 rounded-[12px] px-4 py-3 text-[14px] outline-none focus:border-emerald-500 focus:bg-emerald-50/50 transition-colors" />
          </div>

          <div class="mb-5">
            <label class="block text-[13px] font-bold text-slate-800 mb-2">线路描述</label>
            <textarea v-model="draftRoute.description" placeholder="描述路线亮点、注意事项或补给点" rows="4" class="w-full bg-slate-50 border border-slate-200 rounded-[12px] px-4 py-3 text-[14px] outline-none focus:border-emerald-500 focus:bg-emerald-50/50 transition-colors resize-none"></textarea>
          </div>

          <div class="mb-5">
            <label class="block text-[13px] font-bold text-slate-800 mb-2">添加标签</label>
            <div class="flex flex-wrap gap-2 mb-3">
              <button v-for="tag in availableTags" :key="tag" @click="toggleTag(tag)" :class="draftRoute.tags.includes(tag) ? 'bg-emerald-500 text-white border-emerald-500' : 'bg-white text-slate-600 border-slate-200'" class="px-3 py-1.5 rounded-full text-[12px] font-medium border transition-colors shadow-sm active:scale-95">
                {{ tag }}
              </button>
            </div>
          </div>

          <div class="mb-5">
            <label class="block text-[13px] font-bold text-slate-800 mb-2">难易度预估</label>
            <div class="flex gap-2">
              <button v-for="diff in difficulties" :key="diff" @click="draftRoute.difficulty = diff" :class="draftRoute.difficulty === diff ? 'bg-emerald-500 text-white border-emerald-500' : 'bg-slate-50 text-slate-600 border-slate-200'" class="px-4 py-2 flex-grow rounded-[10px] text-[13px] font-bold border transition-colors">{{ diff }}</button>
            </div>
          </div>

          <div class="mb-5 flex items-center justify-between">
            <label class="text-[13px] font-bold text-slate-800">公开线路</label>
            <button @click="draftRoute.isPublic = !draftRoute.isPublic" :class="draftRoute.isPublic ? 'bg-emerald-500' : 'bg-slate-200'" class="w-11 h-6 rounded-full relative transition-colors duration-300">
              <div :class="draftRoute.isPublic ? 'translate-x-5' : 'translate-x-0'" class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-300"></div>
            </button>
          </div>

          <div v-if="uploadError" class="p-3 bg-red-50 text-red-600 text-[13px] rounded-xl border border-red-100">
            {{ uploadError }}
          </div>

          <div class="h-20"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listRoutes, uploadRoute, type RouteListItem } from '../api'

const router = useRouter()
const fallbackImage = 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80'

const routes = ref<RouteListItem[]>([])
const routeInput = ref<HTMLInputElement | null>(null)
const coverInput = ref<HTMLInputElement | null>(null)
const keyword = ref('')
const visibility = ref('all')
const isLoading = ref(false)
const isUploading = ref(false)
const isSubmitting = ref(false)
const showPublishModal = ref(false)
const selectedFile = ref<File | null>(null)
const coverImage = ref<File | null>(null)
const coverPreviewUrl = ref('')
const error = ref('')
const uploadError = ref('')

const availableTags = ['徒步', '登山', '溯溪', '骑行', '风景好', '挑战', '亲子']
const difficulties = ['轻松', '标准', '困难']

const draftRoute = reactive({
  name: '',
  description: '',
  tags: [] as string[],
  difficulty: '标准',
  isPublic: true,
})

onMounted(loadRoutes)

async function loadRoutes() {
  isLoading.value = true
  error.value = ''
  try {
    const data = await listRoutes({
      keyword: keyword.value,
      visibility: visibility.value,
      page: 1,
      page_size: 50,
    })
    routes.value = data.items
  } catch (e: any) {
    error.value = e.message || '线路列表加载失败'
  } finally {
    isLoading.value = false
  }
}

function clearKeyword() {
  keyword.value = ''
  loadRoutes()
}

function triggerRouteUpload() {
  routeInput.value?.click()
}

function triggerCoverUpload() {
  coverInput.value?.click()
}

function onRouteSelected(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  selectedFile.value = file
  clearCover()
  draftRoute.name = file.name.replace(/\.[^/.]+$/, '')
  draftRoute.description = ''
  draftRoute.tags = []
  draftRoute.difficulty = '标准'
  draftRoute.isPublic = true
  uploadError.value = ''
  showPublishModal.value = true
}

function onCoverSelected(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    uploadError.value = '封面只支持 JPEG、PNG 和 WebP'
    return
  }
  clearCover()
  coverImage.value = file
  coverPreviewUrl.value = URL.createObjectURL(file)
}

async function submitRoute() {
  if (!selectedFile.value || !draftRoute.name.trim()) return

  isSubmitting.value = true
  isUploading.value = true
  uploadError.value = ''
  try {
    const uploaded = await uploadRoute({
      file: selectedFile.value,
      coverImage: coverImage.value,
      name: draftRoute.name.trim(),
      description: draftRoute.description,
      visibility: draftRoute.isPublic ? 'public' : 'private',
      manualTags: {
        labels: draftRoute.tags,
        difficulty: draftRoute.difficulty,
      },
    })
    closeUploadModal()
    await loadRoutes()
    router.push(`/routes/${uploaded.route_id}`)
  } catch (e: any) {
    uploadError.value = e.message || '上传失败'
  } finally {
    isSubmitting.value = false
    isUploading.value = false
  }
}

function closeUploadModal() {
  showPublishModal.value = false
  selectedFile.value = null
  clearCover()
  if (routeInput.value) routeInput.value.value = ''
  if (coverInput.value) coverInput.value.value = ''
}

function clearCover() {
  if (coverPreviewUrl.value) URL.revokeObjectURL(coverPreviewUrl.value)
  coverPreviewUrl.value = ''
  coverImage.value = null
  if (coverInput.value) coverInput.value.value = ''
}

function toggleTag(tag: string) {
  if (draftRoute.tags.includes(tag)) {
    draftRoute.tags = draftRoute.tags.filter((item) => item !== tag)
    return
  }
  if (draftRoute.tags.length < 3) {
    draftRoute.tags.push(tag)
  }
}

function filterClass(value: string) {
  return visibility.value === value
    ? 'bg-emerald-50 text-emerald-700 border-emerald-100'
    : 'bg-slate-50 text-slate-700 border-slate-100'
}

function difficultyLabel(route: RouteListItem) {
  const climbPerKm = route.distance_km > 0 ? route.elevation_gain_m / route.distance_km : 0
  if (climbPerKm >= 100) return '困难'
  if (climbPerKm >= 50) return '标准'
  return '轻松'
}

function difficultyColor(route: RouteListItem) {
  const label = difficultyLabel(route)
  if (label === '轻松') return 'bg-[#B4E195]'
  if (label === '标准') return 'bg-[#DCE775]'
  return 'bg-[#FBC02D]'
}

function estimateDuration(route: RouteListItem) {
  const hours = route.distance_km / 3.2 + route.elevation_gain_m / 450
  const totalMinutes = Math.max(10, Math.round(hours * 60))
  const h = Math.floor(totalMinutes / 60)
  const m = totalMinutes % 60
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

function formatKm(value: number) {
  return value.toFixed(value >= 10 ? 1 : 2)
}

function formatFileSize(size: number) {
  if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}
</script>

<style scoped>
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
