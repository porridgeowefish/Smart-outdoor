<template>
  <div class="flex flex-col h-[100dvh] bg-[#f8f9fa] relative overflow-hidden z-[100] absolute inset-0">
    <div class="absolute top-0 left-0 right-0 h-14 flex items-center justify-between px-4 z-20">
      <button @click="$router.back()" class="w-8 h-8 flex items-center justify-center bg-black/30 backdrop-blur-md text-white rounded-full hover:bg-black/50 transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
      </button>
      <div class="flex items-center gap-2">
        <button class="w-8 h-8 flex items-center justify-center bg-black/30 backdrop-blur-md text-white rounded-full hover:bg-black/50 transition-colors">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" x2="15.42" y1="13.51" y2="17.49"/><line x1="15.41" x2="8.59" y1="6.51" y2="10.49"/></svg>
        </button>
      </div>
    </div>

    <div class="w-full h-[45%] bg-[#d3d9df] relative shrink-0">
      <div v-if="loading" class="w-full h-full flex items-center justify-center bg-slate-200">
        <span class="animate-spin w-7 h-7 border-2 border-emerald-100 border-t-emerald-500 rounded-full"></span>
      </div>
      <RouteAmap
        v-else-if="routeData"
        :geojson="routeData.track.geojson"
        :coordinate-system="routeData.track.coordinate_system"
      />
      <div v-else class="w-full h-full flex items-center justify-center bg-slate-200 text-slate-600 text-[13px] px-8 text-center">
        {{ error || '线路详情加载失败' }}
      </div>
      <div class="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-white to-transparent pointer-events-none"></div>
    </div>

    <div class="flex-grow bg-white rounded-t-[20px] -mt-5 z-10 relative flex flex-col shadow-[0_-4px_16px_rgba(0,0,0,0.06)] overflow-y-auto">
      <div class="w-full py-2 flex justify-center shrink-0">
        <div class="w-10 h-1.5 bg-slate-200 rounded-full"></div>
      </div>

      <div v-if="routeData" class="px-5 pb-24 flex-grow">
        <div class="flex justify-between items-start mb-2">
          <h1 class="text-[20px] font-bold text-slate-800 leading-tight pr-4">{{ routeData.name }}</h1>
        </div>

        <div class="flex items-center gap-1.5 mb-6">
          <span :class="difficultyColor" class="text-slate-800 text-[10px] px-1.5 py-0.5 rounded font-bold tracking-wide">
            {{ difficultyLabel }}
          </span>
          <span class="text-[12px] text-slate-400 font-medium">{{ routeData.visibility === 'public' ? '公开线路' : '私有线路' }}</span>
          <span class="text-[12px] text-slate-500 font-medium">{{ routeData.track.point_count }} 点</span>
        </div>

        <div class="grid grid-cols-3 gap-y-6 gap-x-2 text-center mb-8 border-b border-slate-100 pb-6">
          <div>
            <div class="text-[20px] font-bold text-slate-800 flex items-baseline justify-center gap-0.5">
              {{ formatKm(routeData.analysis.distance_km) }} <span class="text-[11px] font-normal text-slate-500">km</span>
            </div>
            <div class="text-[11px] text-slate-400 mt-1">里程</div>
          </div>
          <div>
            <div class="text-[20px] font-bold text-slate-800 flex items-baseline justify-center gap-0.5">
              {{ Math.round(routeData.analysis.elevation_gain_m) }} <span class="text-[11px] font-normal text-slate-500">m</span>
            </div>
            <div class="text-[11px] text-slate-400 mt-1">累计爬升</div>
          </div>
          <div>
            <div class="text-[20px] font-bold text-slate-800 flex items-baseline justify-center gap-0.5">
              {{ estimatedDuration.hours }}<span class="text-[11px] font-normal text-slate-500 mr-0.5">h</span>{{ estimatedDuration.minutes }}<span class="text-[11px] font-normal text-slate-500">m</span>
            </div>
            <div class="text-[11px] text-slate-400 mt-1">预计耗时</div>
          </div>

          <div>
            <div class="text-[18px] font-semibold text-slate-800 flex items-baseline justify-center gap-0.5">
              {{ valueOrDash(routeData.analysis.elevation_max_m) }} <span class="text-[11px] font-normal text-slate-500">m</span>
            </div>
            <div class="text-[11px] text-slate-400 mt-1">最高海拔</div>
          </div>
          <div>
            <div class="text-[18px] font-semibold text-slate-800 flex items-baseline justify-center gap-0.5">
              {{ valueOrDash(routeData.analysis.elevation_min_m) }} <span class="text-[11px] font-normal text-slate-500">m</span>
            </div>
            <div class="text-[11px] text-slate-400 mt-1">最低海拔</div>
          </div>
          <div>
            <div class="text-[18px] font-semibold text-slate-800 flex items-baseline justify-center gap-0.5">
              {{ routeData.analysis.climb_ratio ?? '-' }} <span class="text-[11px] font-normal text-slate-500">m/km</span>
            </div>
            <div class="text-[11px] text-slate-400 mt-1">爬升强度</div>
          </div>
        </div>

        <div v-if="routeData.description" class="mb-8">
          <h3 class="text-[15px] font-bold text-slate-800 mb-2">线路描述</h3>
          <p class="text-[13px] text-slate-600 leading-6">{{ routeData.description }}</p>
        </div>

        <div>
          <div class="flex justify-between items-center mb-3">
            <h3 class="text-[15px] font-bold text-slate-800">海拔剖面</h3>
            <span class="text-[12px] text-slate-500 font-medium">{{ elevationRangeText }}</span>
          </div>

          <div class="h-[140px] bg-white border border-slate-200 rounded-xl relative p-3 overflow-hidden">
            <div class="absolute inset-0 flex flex-col justify-between p-3 opacity-20 pointer-events-none">
              <div class="border-b border-slate-300 w-full h-0"></div>
              <div class="border-b border-slate-300 w-full h-0"></div>
              <div class="border-b border-slate-300 w-full h-0"></div>
              <div class="border-b border-slate-300 w-full h-0"></div>
            </div>
            <span class="absolute top-2 left-2 text-[10px] text-slate-400 bg-white/80 px-1">{{ valueOrDash(routeData.analysis.elevation_max_m) }}m</span>
            <span class="absolute bottom-2 left-2 text-[10px] text-slate-400 bg-white/80 px-1">{{ valueOrDash(routeData.analysis.elevation_min_m) }}m</span>

            <svg v-if="elevationPath" class="w-full h-full absolute bottom-0 left-0" viewBox="0 0 100 50" preserveAspectRatio="none">
              <linearGradient id="elevGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#10b981" stop-opacity="0.3"></stop>
                <stop offset="100%" stop-color="#10b981" stop-opacity="0.05"></stop>
              </linearGradient>
              <path :d="`${elevationPath} L 100,50 L 0,50 Z`" fill="url(#elevGrad)"></path>
              <path :d="elevationPath" fill="none" stroke="#10b981" stroke-width="1.5" vector-effect="non-scaling-stroke"></path>
            </svg>
            <div v-else class="h-full flex items-center justify-center text-[12px] text-slate-400">无海拔数据</div>
          </div>
        </div>

        <div class="mt-8">
          <h3 class="text-[15px] font-bold text-slate-800 mb-3">包含标签</h3>
          <div class="flex flex-wrap gap-2">
            <span v-for="tag in displayTags" :key="tag" class="bg-slate-100 text-slate-600 text-[12px] px-3 py-1.5 rounded-full font-medium">{{ tag }}</span>
            <span v-if="displayTags.length === 0" class="text-[12px] text-slate-400">暂无标签</span>
          </div>
        </div>
      </div>
    </div>

    <div class="absolute bottom-0 left-0 right-0 p-3 bg-white border-t border-slate-100 shadow-[0_-5px_20px_rgba(0,0,0,0.03)] pb-safe z-20 flex gap-3">
      <button class="w-12 h-[48px] shrink-0 bg-slate-100 text-slate-600 rounded-xl flex items-center justify-center hover:bg-slate-200 transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
      </button>
      <button @click="forwardToChat" :disabled="!routeData" class="flex-grow h-[48px] bg-emerald-500 text-white font-bold rounded-[14px] flex items-center justify-center gap-2 hover:bg-emerald-600 transition-colors shadow-sm active:scale-[0.98] disabled:opacity-50">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
        发送至“出去走走”
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import RouteAmap from '../components/RouteAmap.vue'
import { clearAuthToken, getRouteDetail, type RouteDetailResponse } from '../api'
import { extractLineCoordinates } from '../utils/routeTrack'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const routeData = ref<RouteDetailResponse | null>(null)

onMounted(loadDetail)

async function loadDetail() {
  loading.value = true
  error.value = ''
  try {
    routeData.value = await getRouteDetail(route.params.id as string)
  } catch (e: any) {
    error.value = e.message || '线路详情加载失败'
    if (e.status === 401) {
      clearAuthToken()
      router.replace({ path: '/login', query: { redirect: route.fullPath } })
    }
  } finally {
    loading.value = false
  }
}

const difficultyLabel = computed(() => {
  if (!routeData.value) return '标准'
  const climbPerKm = routeData.value.analysis.distance_km > 0
    ? routeData.value.analysis.elevation_gain_m / routeData.value.analysis.distance_km
    : 0
  if (climbPerKm >= 100) return '困难'
  if (climbPerKm >= 50) return '标准'
  return '轻松'
})

const difficultyColor = computed(() => {
  if (difficultyLabel.value === '轻松') return 'bg-[#B4E195]'
  if (difficultyLabel.value === '标准') return 'bg-[#DCE775]'
  return 'bg-[#FBC02D]'
})

const estimatedDuration = computed(() => {
  if (!routeData.value) return { hours: '0', minutes: '00' }
  const hours = routeData.value.analysis.distance_km / 3.2 + routeData.value.analysis.elevation_gain_m / 450
  const totalMinutes = Math.max(10, Math.round(hours * 60))
  return {
    hours: String(Math.floor(totalMinutes / 60)),
    minutes: String(totalMinutes % 60).padStart(2, '0'),
  }
})

const displayTags = computed(() => {
  if (!routeData.value) return []
  const values = Object.values(routeData.value.manual_tags || {})
  return values.flatMap((value) => {
    if (Array.isArray(value)) return value.map(String)
    if (typeof value === 'string' && value) return [value]
    return []
  }).slice(0, 8)
})

const elevationPath = computed(() => {
  if (!routeData.value) return ''
  const coordinates = extractLineCoordinates(routeData.value.track.geojson)
  const points = coordinates.filter((point) => typeof point[2] === 'number')
  if (points.length < 2) return ''
  const elevations = points.map((point) => point[2] as number)
  const min = Math.min(...elevations)
  const max = Math.max(...elevations)
  if (max === min) return ''
  return points.map((point, index) => {
    const x = points.length === 1 ? 0 : index / (points.length - 1) * 100
    const y = 46 - (((point[2] as number) - min) / (max - min)) * 40
    return `${index === 0 ? 'M' : 'L'} ${x.toFixed(2)},${y.toFixed(2)}`
  }).join(' ')
})

const elevationRangeText = computed(() => {
  if (!routeData.value) return ''
  const min = routeData.value.analysis.elevation_min_m
  const max = routeData.value.analysis.elevation_max_m
  if (min === null || max === null) return '无海拔数据'
  return `${Math.round(min)}m - ${Math.round(max)}m`
})

function forwardToChat() {
  if (!routeData.value) return
  router.push({
    path: '/chat',
    query: {
      seed: `我想围绕这条线路安排行程：${routeData.value.name}，里程 ${formatKm(routeData.value.analysis.distance_km)}km，爬升 ${Math.round(routeData.value.analysis.elevation_gain_m)}m。`,
    },
  })
}

function formatKm(value: number) {
  return value.toFixed(value >= 10 ? 1 : 2)
}

function valueOrDash(value: number | null) {
  return value === null ? '-' : Math.round(value)
}
</script>

<style scoped>
.pb-safe {
  padding-bottom: env(safe-area-inset-bottom);
}
</style>
