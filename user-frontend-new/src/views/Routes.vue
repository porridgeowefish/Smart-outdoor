<template>
  <div class="relative flex h-full flex-col bg-slate-50">
    <header class="sticky top-0 z-10 flex h-[44px] shrink-0 items-center justify-between border-b border-slate-100 bg-white px-4 shadow-sm">
      <div class="flex items-center gap-3">
        <h1 class="text-[18px] font-bold text-slate-800">线路</h1>
        <span class="text-[12px] font-medium text-slate-400">真实数据</span>
      </div>
      <button
        class="flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1.5 text-[12px] font-bold text-emerald-600 transition-colors hover:bg-emerald-100 disabled:opacity-60"
        :disabled="isUploading"
        @click="triggerRouteUpload"
      >
        <span v-if="isUploading" class="h-3 w-3 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-500"></span>
        <span v-else class="text-base leading-none">+</span>
        {{ isUploading ? '上传中...' : '发布线路' }}
      </button>
      <input ref="routeInput" type="file" class="hidden" accept=".kml,.gpx,.geojson,.json" @change="onRouteSelected" />
      <input ref="coverInput" type="file" class="hidden" accept="image/jpeg,image/png,image/webp" @change="onCoverSelected" />
    </header>

    <section class="sticky top-[44px] z-10 shrink-0 bg-white px-3 pb-2 pt-3">
      <div class="mb-3 flex gap-2">
        <div class="relative flex-grow">
          <input
            v-model.trim="keyword"
            type="text"
            placeholder="搜索线路名称"
            class="w-full rounded-full border border-transparent bg-slate-50 py-2 pl-4 pr-4 text-[13px] outline-none transition-colors placeholder:text-slate-400 focus:border-emerald-500 focus:bg-white"
            @keyup.enter="loadRoutes"
          />
        </div>
        <button class="shrink-0 px-2 text-[12px] font-bold text-slate-400" @click="clearKeyword">清空</button>
      </div>

      <div class="hide-scrollbar flex gap-2 overflow-x-auto pb-1 text-[13px]">
        <button class="filter-btn" :class="filterClass('all')" @click="setVisibility('all')">全部</button>
        <button class="filter-btn" :class="filterClass('public')" @click="setVisibility('public')">公开</button>
        <button class="filter-btn" :class="filterClass('private')" @click="setVisibility('private')">我的私有</button>
      </div>
    </section>

    <main class="flex-grow overflow-y-auto bg-slate-50 px-3 py-3">
      <div v-if="isLoading" class="flex justify-center py-16">
        <span class="h-6 w-6 animate-spin rounded-full border-2 border-emerald-100 border-t-emerald-500"></span>
      </div>

      <div v-else-if="error" class="rounded-xl border border-red-100 bg-red-50 p-4 text-[13px] text-red-600">
        {{ error }}
      </div>

      <div v-else-if="routes.length === 0" class="px-8 py-16 text-center">
        <h3 class="mb-1 text-[16px] font-bold text-slate-800">还没有线路</h3>
        <p class="text-[13px] text-slate-500">上传 KML、GPX 或 GeoJSON 后，这里会显示数据库里的真实线路。</p>
      </div>

      <div v-else>
        <button
          v-for="route in routes"
          :key="route.route_id"
          class="mb-3 flex w-full gap-3 rounded-2xl bg-white p-3 text-left shadow-sm transition-transform active:scale-[0.98]"
          @click="router.push(`/routes/${route.route_id}`)"
        >
          <div class="relative h-[105px] w-[105px] shrink-0 overflow-hidden rounded-xl bg-slate-100">
            <RoutePreviewCard
              :track-preview="route.track_preview"
              :distance-km="route.distance_km"
              :elevation-gain-m="route.elevation_gain_m"
            />
            <div class="absolute left-0 top-0 rounded-br-lg px-1.5 py-0.5 text-[10px] font-bold text-slate-800 opacity-90" :class="difficultyColor(route)">
              {{ difficultyLabel(route) }}
            </div>
          </div>

          <div class="flex min-w-0 flex-grow flex-col justify-between py-0.5">
            <div>
              <h3 class="mb-1.5 line-clamp-2 pr-1 text-[15px] font-bold leading-snug text-slate-800">{{ route.name }}</h3>
              <p v-if="route.location" class="mb-1.5 line-clamp-1 text-[11px] text-slate-400">{{ route.location }}</p>
              <div class="mb-2 flex flex-wrap items-center gap-x-2.5 gap-y-1 text-[11px] font-medium text-slate-500">
                <span>{{ formatKm(route.distance_km) }} 公里</span>
                <span>{{ Math.round(route.elevation_gain_m) }} 米爬升</span>
                <span>{{ estimateDuration(route) }}</span>
              </div>
            </div>

            <div class="mt-auto flex flex-wrap items-center gap-1.5">
              <span v-for="tag in route.display_tags" :key="tag" class="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600">{{ tag }}</span>
              <span class="ml-auto rounded px-1.5 py-0.5 text-[10px] font-medium" :class="route.visibility === 'public' ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-500'">
                {{ route.visibility === 'public' ? '公开' : '私有' }}
              </span>
            </div>
          </div>
        </button>
      </div>
    </main>

    <section v-if="showPublishModal" class="absolute inset-0 z-50 flex flex-col bg-white">
      <header class="flex h-14 shrink-0 items-center justify-between border-b border-slate-100 px-4">
        <button class="font-medium text-slate-500" @click="closeUploadModal">取消</button>
        <h2 class="text-[16px] font-bold text-slate-800">编辑线路</h2>
        <button class="font-bold text-emerald-500 disabled:opacity-50" :disabled="isSubmitting || !draftRoute.name.trim()" @click="submitRoute">
          {{ isSubmitting ? '保存中...' : '发布' }}
        </button>
      </header>

      <div class="flex-grow overflow-y-auto">
        <div class="relative h-[220px] bg-slate-900">
          <img v-if="coverPreviewUrl" :src="coverPreviewUrl" class="h-full w-full object-cover opacity-75" alt="" />
          <div v-else class="h-full w-full">
            <RoutePreviewCard show-stats />
          </div>
          <div class="absolute right-3 top-3 flex gap-2">
            <button class="rounded-full bg-white/90 px-3 py-1.5 text-[12px] font-bold text-slate-700 shadow" @click="triggerCoverUpload">
              {{ coverImage ? '更换封面' : '选择封面' }}
            </button>
            <button v-if="coverImage" class="rounded-full bg-black/45 px-3 py-1.5 text-[12px] font-bold text-white shadow" @click="clearCover">
              清除
            </button>
          </div>
          <div class="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-900 to-transparent px-4 pb-3 pt-12 text-white">
            <div class="mb-1 text-[11px] font-bold uppercase tracking-wider text-white/70">待上传文件</div>
            <div class="truncate text-[18px] font-bold leading-tight">{{ selectedFile?.name }}</div>
            <div class="mt-1 text-[12px] text-white/70">{{ selectedFile ? formatFileSize(selectedFile.size) : '' }}</div>
          </div>
        </div>

        <div class="p-5">
          <div class="mb-5">
            <label class="mb-2 block text-[13px] font-bold text-slate-800">线路名称 <span class="text-red-500">*</span></label>
            <input v-model="draftRoute.name" type="text" placeholder="给线路起一个名字" class="form-input" />
          </div>

          <div class="mb-5">
            <label class="mb-2 block text-[13px] font-bold text-slate-800">线路描述</label>
            <textarea v-model="draftRoute.description" placeholder="描述路线亮点、注意事项或补给点" rows="4" class="form-input resize-none"></textarea>
          </div>

          <div class="mb-5">
            <div class="mb-2 flex items-center justify-between">
              <label class="block text-[13px] font-bold text-slate-800">多维标签</label>
              <span class="text-[11px] font-medium text-slate-400">按分类多选</span>
            </div>
            <div v-if="taxonomyLoading" class="rounded-xl bg-slate-50 p-4 text-[13px] text-slate-500">正在加载标签...</div>
            <div v-else-if="taxonomyError" class="rounded-xl bg-red-50 p-4 text-[13px] text-red-500">{{ taxonomyError }}</div>
            <div v-else class="space-y-4">
              <section v-for="category in tagCategories" :key="category.key">
                <h3 class="mb-2 text-[12px] font-black text-slate-500">{{ category.label }}</h3>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="tag in category.tags"
                    :key="`${category.key}-${tag}`"
                    class="rounded-full border px-3 py-1.5 text-[12px] font-medium shadow-sm transition-colors active:scale-95"
                    :class="isTagSelected(category.key, tag) ? 'border-emerald-500 bg-emerald-500 text-white' : 'border-slate-200 bg-white text-slate-600'"
                    @click="toggleTag(category.key, tag)"
                  >
                    {{ tag }}
                  </button>
                </div>
              </section>
            </div>
          </div>

          <div class="mb-5">
            <label class="mb-2 block text-[13px] font-bold text-slate-800">难易度预估</label>
            <div class="flex gap-2">
              <button
                v-for="diff in difficulties"
                :key="diff"
                class="flex-grow rounded-xl border px-4 py-2 text-[13px] font-bold transition-colors"
                :class="draftRoute.difficulty === diff ? 'border-emerald-500 bg-emerald-500 text-white' : 'border-slate-200 bg-slate-50 text-slate-600'"
                @click="draftRoute.difficulty = diff"
              >
                {{ diff }}
              </button>
            </div>
          </div>

          <div class="mb-5 flex items-center justify-between">
            <label class="text-[13px] font-bold text-slate-800">公开线路</label>
            <button class="relative h-6 w-11 rounded-full transition-colors duration-300" :class="draftRoute.isPublic ? 'bg-emerald-500' : 'bg-slate-200'" @click="draftRoute.isPublic = !draftRoute.isPublic">
              <div class="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform duration-300" :class="draftRoute.isPublic ? 'translate-x-5' : 'translate-x-0'"></div>
            </button>
          </div>

          <div v-if="uploadError" class="rounded-xl border border-red-100 bg-red-50 p-3 text-[13px] text-red-600">
            {{ uploadError }}
          </div>
          <div class="h-20"></div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  getRouteTagTaxonomy,
  listRoutes,
  uploadRoute,
  type RouteListItem,
  type RouteTagTaxonomyResponse,
} from '../api'
import RoutePreviewCard from '../components/RoutePreviewCard.vue'

type TagCategory = RouteTagTaxonomyResponse['categories'][number]

const router = useRouter()

const routes = ref<RouteListItem[]>([])
const tagCategories = ref<TagCategory[]>([])
const routeInput = ref<HTMLInputElement | null>(null)
const coverInput = ref<HTMLInputElement | null>(null)
const keyword = ref('')
const visibility = ref('all')
const isLoading = ref(false)
const taxonomyLoading = ref(false)
const isUploading = ref(false)
const isSubmitting = ref(false)
const showPublishModal = ref(false)
const selectedFile = ref<File | null>(null)
const coverImage = ref<File | null>(null)
const coverPreviewUrl = ref('')
const error = ref('')
const uploadError = ref('')
const taxonomyError = ref('')

const difficulties = ['轻松', '标准', '困难']

const draftRoute = reactive({
  name: '',
  description: '',
  tags: {} as Record<string, string[]>,
  difficulty: '标准',
  isPublic: true,
})

onMounted(async () => {
  await Promise.all([loadRoutes(), loadTagTaxonomy()])
})

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
  } catch (e) {
    error.value = e instanceof Error ? e.message : '线路列表加载失败'
  } finally {
    isLoading.value = false
  }
}

async function loadTagTaxonomy() {
  taxonomyLoading.value = true
  taxonomyError.value = ''
  try {
    const data = await getRouteTagTaxonomy()
    tagCategories.value = data.categories
  } catch (e) {
    taxonomyError.value = e instanceof Error ? e.message : '标签加载失败'
  } finally {
    taxonomyLoading.value = false
  }
}

function clearKeyword() {
  keyword.value = ''
  loadRoutes()
}

function setVisibility(value: string) {
  visibility.value = value
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
  draftRoute.tags = {}
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
        ...selectedManualTags(),
        difficulty: [draftRoute.difficulty],
      },
    })
    closeUploadModal()
    await loadRoutes()
    router.push(`/routes/${uploaded.route_id}`)
  } catch (e) {
    uploadError.value = e instanceof Error ? e.message : '上传失败'
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

function toggleTag(categoryKey: string, tag: string) {
  const current = draftRoute.tags[categoryKey] || []
  if (current.includes(tag)) {
    draftRoute.tags[categoryKey] = current.filter((item) => item !== tag)
    if (draftRoute.tags[categoryKey].length === 0) delete draftRoute.tags[categoryKey]
    return
  }
  draftRoute.tags[categoryKey] = [...current, tag]
}

function isTagSelected(categoryKey: string, tag: string) {
  return (draftRoute.tags[categoryKey] || []).includes(tag)
}

function selectedManualTags() {
  return Object.fromEntries(
    Object.entries(draftRoute.tags).filter(([, values]) => values.length > 0),
  )
}

function filterClass(value: string) {
  return visibility.value === value
    ? 'border-emerald-100 bg-emerald-50 text-emerald-700'
    : 'border-slate-100 bg-slate-50 text-slate-700'
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
.filter-btn {
  flex-shrink: 0;
  border-radius: 9999px;
  border-width: 1px;
  padding: 0.375rem 0.75rem;
  font-weight: 500;
}
.form-input {
  width: 100%;
  border-radius: 0.75rem;
  border: 1px solid rgb(226 232 240);
  background: rgb(248 250 252);
  padding: 0.75rem 1rem;
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s, background-color 0.15s;
}
.form-input:focus {
  border-color: rgb(16 185 129);
  background: rgb(236 253 245 / 0.5);
}
</style>
