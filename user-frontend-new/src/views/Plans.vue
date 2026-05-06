<template>
  <div class="flex h-[100dvh] flex-col bg-slate-50 font-sans">
    <div class="sticky top-0 z-10 flex h-14 shrink-0 items-center border-b border-slate-200 bg-white px-5 text-center shadow-sm">
      <h1 class="w-full text-[18px] font-bold tracking-wide text-slate-800">我的规划</h1>
    </div>

    <div class="flex-grow overflow-y-auto pb-[90px]">
      <div v-if="isLoading" class="p-8 pt-20 text-center text-[13px] font-medium text-slate-500">
        正在加载我的规划...
      </div>

      <div v-else-if="errorMessage" class="p-8 pt-20 text-center">
        <p class="mb-5 text-[13px] font-medium text-red-500">{{ errorMessage }}</p>
        <button class="bg-slate-900 px-6 py-3 text-[14px] font-bold text-white" @click="loadSnapshots">重试</button>
      </div>

      <div v-else-if="snapshots.length === 0" class="flex flex-col items-center justify-center p-8 pt-20">
        <div class="mb-6 flex h-16 w-16 items-center justify-center bg-slate-100 shadow-inner">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="text-slate-400"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="m16 13-3.5 3.5-2-2"/></svg>
        </div>
        <h2 class="mb-2 text-[16px] font-bold text-slate-800">还没有保存规划</h2>
        <p class="mb-8 px-4 text-center text-[13px] leading-relaxed text-slate-500">在“出去走走”中打开候选线路后，<br />可以将其保存到这里方便随时查看。</p>
        <button class="w-[200px] bg-slate-900 px-8 py-3.5 text-[14px] font-bold text-white shadow-sm active:scale-[0.98]" @click="router.push('/chat')">
          去发现路线
        </button>
      </div>

      <div v-else class="mt-2 flex flex-col border-b border-slate-200 bg-white">
        <div
          v-for="snapshot in snapshots"
          :key="snapshot.snapshot_id"
          class="relative flex cursor-pointer gap-4 border-t border-slate-100 p-4 transition-colors active:bg-slate-50"
          @click="router.push(`/plans/${snapshot.snapshot_id}`)"
        >
          <div class="relative h-[80px] w-[100px] shrink-0 border border-slate-200/60 bg-slate-100 shadow-[inset_0_0_0_1px_rgba(0,0,0,0.05)]">
            <img v-if="snapshot.route.cover_image_url" :src="snapshot.route.cover_image_url" class="h-full w-full object-cover" alt="" />
            <div v-else class="flex h-full w-full items-center justify-center bg-gradient-to-br from-emerald-50 to-slate-100 text-[11px] font-black text-emerald-600">
              {{ formatNumber(snapshot.route.distance_km, 1) }}km
            </div>
          </div>

          <div class="flex min-w-0 flex-grow flex-col justify-between py-0.5">
            <div>
              <h3 class="mb-1 line-clamp-1 text-[15px] font-bold tracking-tight text-slate-800">{{ snapshot.route.name }}</h3>
              <div class="mb-2 flex gap-3 text-[12px] font-medium text-slate-500">
                <span><span class="mr-0.5 text-slate-400">里程</span>{{ formatNumber(snapshot.route.distance_km, 1) }}km</span>
                <span><span class="mr-0.5 text-slate-400">爬升</span>{{ formatNumber(snapshot.route.elevation_gain_m, 0) }}m</span>
              </div>
            </div>

            <div class="flex items-center justify-between gap-3">
              <div class="flex flex-wrap gap-1.5">
                <span v-for="tag in snapshot.advantage_tags" :key="tag" class="bg-slate-100 px-1.5 py-[2px] text-[11px] font-medium text-slate-500">
                  {{ tag }}
                </span>
              </div>
              <div class="whitespace-nowrap text-[11px] font-medium text-slate-400">{{ formatDate(snapshot.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listRoutePlanSnapshots, type RoutePlanSnapshotItem } from '../api'

const router = useRouter()
const snapshots = ref<RoutePlanSnapshotItem[]>([])
const isLoading = ref(false)
const errorMessage = ref('')

onMounted(loadSnapshots)

async function loadSnapshots() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await listRoutePlanSnapshots()
    snapshots.value = response.items
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '获取我的规划失败'
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
