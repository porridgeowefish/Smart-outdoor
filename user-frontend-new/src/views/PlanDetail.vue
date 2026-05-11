<template>
  <div class="absolute inset-0 z-[100] flex h-[100dvh] flex-col overflow-hidden bg-[#f8f9fa] font-sans">
    <div class="absolute left-0 right-0 top-0 z-20 flex h-14 items-center justify-between px-4">
      <button class="flex h-8 w-8 items-center justify-center bg-black/40 text-white shadow-sm backdrop-blur-md" @click="router.back()">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m15 18-6-6 6-6"/></svg>
      </button>
      <span class="text-[13px] font-bold tracking-widest text-white drop-shadow-md">保存规划</span>
      <div class="w-8"></div>
    </div>

    <div class="relative h-[35%] w-full shrink-0 bg-slate-900">
      <img v-if="snapshot?.route.cover_image_url" :src="snapshot.route.cover_image_url" class="h-full w-full object-cover opacity-75" alt="" />
      <div v-else class="h-full w-full bg-gradient-to-br from-slate-900 via-emerald-900 to-slate-800"></div>
      <div class="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white to-transparent"></div>
    </div>

    <div class="relative z-10 -mt-6 flex flex-grow flex-col overflow-y-auto bg-white shadow-[0_-4px_24px_rgba(0,0,0,0.08)]">
      <div v-if="isLoading" class="p-6 pt-10 text-center text-[13px] font-medium text-slate-500">正在加载规划详情...</div>
      <div v-else-if="errorMessage" class="p-6 pt-10 text-center">
        <p class="mb-5 text-[13px] font-medium text-red-500">{{ errorMessage }}</p>
        <button class="bg-slate-900 px-6 py-3 text-[14px] font-bold text-white" @click="loadSnapshot">重试</button>
      </div>

      <div v-else-if="snapshot" class="p-6">
        <h2 class="mb-2 text-[22px] font-black leading-tight tracking-tight text-slate-900">{{ snapshot.route.name }}</h2>
        <p class="mb-6 flex gap-1.5 border-b border-slate-100 pb-4 text-[13px] font-bold tracking-wide text-slate-500">
          保存时间：{{ formatDate(snapshot.created_at) }}
        </p>

        <div class="mb-6 grid grid-cols-3 divide-x divide-slate-200/60 border-y border-slate-100 bg-slate-50">
          <div class="p-3 text-center">
            <div class="mb-1 font-mono text-[20px] font-black leading-none text-slate-800">{{ formatNumber(snapshot.route.distance_km, 1) }}</div>
            <div class="text-[11px] font-bold tracking-wider text-slate-400">总里程 (KM)</div>
          </div>
          <div class="p-3 text-center">
            <div class="mb-1 font-mono text-[20px] font-black leading-none text-slate-800">{{ formatNumber(snapshot.route.elevation_gain_m, 0) }}</div>
            <div class="text-[11px] font-bold tracking-wider text-slate-400">爬升 (M)</div>
          </div>
          <div class="p-3 text-center">
            <div class="mb-1 font-mono text-[16px] font-black leading-none text-blue-600">{{ snapshot.planning_detail.estimated_duration || '未估算' }}</div>
            <div class="text-[11px] font-bold tracking-wider text-slate-400">预估耗时</div>
          </div>
        </div>

        <div class="mb-6 border-l-4 border-indigo-500 bg-indigo-50/50 p-4">
          <h3 class="mb-2 text-[15px] font-bold tracking-tight text-slate-800">为何推荐</h3>
          <p class="text-justify text-[13.5px] font-medium leading-relaxed text-slate-700">{{ snapshot.recommendation_reason }}</p>
        </div>

        <div class="mb-6 space-y-3 text-[13px] leading-relaxed text-slate-600">
          <p><span class="font-bold text-slate-800">规划说明：</span>{{ snapshot.planning_detail.summary || '暂无说明' }}</p>
          <p><span class="font-bold text-slate-800">天气：</span>{{ snapshot.evidence.weather?.summary || '未确认' }}</p>
          <p><span class="font-bold text-slate-800">交通：</span>{{ snapshot.evidence.transport?.summary || '未确认' }}</p>
          <p><span class="font-bold text-slate-800">近期路况：</span>{{ snapshot.evidence.web_evidence?.summary || '未确认' }}</p>
        </div>

        <div class="mb-6 border border-slate-200 p-4 shadow-sm">
          <div class="mb-2 flex items-center gap-2 text-[14px] font-bold text-slate-900">
            <span class="h-2 w-2 rounded-full bg-red-500"></span>
            风险提醒
          </div>
          <ul class="space-y-1 text-[13px] font-medium leading-relaxed text-slate-600">
            <li v-for="note in riskNotes" :key="note">{{ note }}</li>
          </ul>
        </div>

        <button class="mb-3 w-full bg-emerald-500 px-5 py-3.5 text-[14px] font-bold text-white" @click="router.push(`/routes/${snapshot.route.route_id}`)">
          查看线路详情
        </button>
        <button class="mb-8 w-full bg-slate-900 px-5 py-3.5 text-[14px] font-bold text-white" @click="router.push('/chat')">
          回到出去走走
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getRoutePlanSnapshotDetail, type RoutePlanSnapshotDetailResponse } from '../api'

const route = useRoute()
const router = useRouter()
const snapshot = ref<RoutePlanSnapshotDetailResponse | null>(null)
const isLoading = ref(false)
const errorMessage = ref('')

const riskNotes = computed(() => {
  const notes = snapshot.value?.planning_detail.risk_notes
  return Array.isArray(notes) && notes.length ? notes.map(String) : ['近期路况未确认，出发前需要再次核实。']
})

onMounted(loadSnapshot)

async function loadSnapshot() {
  const id = String(route.params.id || '')
  isLoading.value = true
  errorMessage.value = ''
  try {
    snapshot.value = await getRoutePlanSnapshotDetail(id)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '获取规划详情失败'
  } finally {
    isLoading.value = false
  }
}

function formatNumber(value: number, digits: number) {
  return value.toFixed(digits)
}

function formatDate(value: string) {
  return value.slice(0, 10)
}
</script>
