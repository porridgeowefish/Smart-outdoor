<template>
  <div class="flex flex-col h-[100dvh] bg-slate-50 font-sans">
    <div class="h-14 bg-white border-b border-slate-200 flex items-center px-5 shrink-0 shadow-sm z-10 sticky top-0 text-center relative">
      <h1 class="text-[18px] font-bold text-slate-800 tracking-wide w-[100%]">我的规划</h1>
    </div>

    <div class="flex-grow overflow-y-auto pb-[90px]">
      <div v-if="mockPlans.length === 0" class="flex flex-col items-center justify-center p-8 pt-20">
        <div class="w-16 h-16 bg-slate-100 flex items-center justify-center mb-6 shadow-inner">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-slate-400"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="m16 13-3.5 3.5-2-2"/></svg>
        </div>
        <h2 class="text-[16px] font-bold text-slate-800 mb-2">还没有保存规划</h2>
        <p class="text-slate-500 text-[13px] leading-relaxed mb-8 text-center px-4">在“对话助手”中规划路线后，<br/>可以将其保存到这里方便随时查看。</p>
        <button @click="$router.push('/chat')" class="bg-slate-900 text-white px-8 py-3.5 font-bold text-[14px] shadow-sm hover:bg-slate-800 active:scale-[0.98] transition-transform w-[200px]">
          去发现路线
        </button>
      </div>

      <div v-else class="flex flex-col bg-white border-b border-slate-200 mt-2">
        <div v-for="plan in mockPlans" :key="plan.id" @click="$router.push(`/plans/${plan.id}`)" class="flex gap-4 p-4 border-t border-slate-100 active:bg-slate-50 cursor-pointer transition-colors relative">
          <!-- Thumbnail -->
          <div class="w-[100px] h-[80px] bg-slate-100 shrink-0 relative border border-slate-200/60 shadow-[inset_0_0_0_1px_rgba(0,0,0,0.05)]">
            <img :src="plan.img" class="w-full h-full object-cover" />
          </div>
          
          <!-- Content -->
          <div class="flex-grow min-w-0 py-0.5 flex flex-col justify-between">
            <div>
              <h3 class="font-bold text-slate-800 text-[15px] mb-1 line-clamp-1 tracking-tight">{{ plan.name }}</h3>
              <div class="text-[12px] font-medium text-slate-500 flex gap-3 mb-2">
                 <span><span class="text-slate-400 mr-0.5">里程</span>{{ plan.distance }}km</span>
                 <span><span class="text-slate-400 mr-0.5">爬升</span>{{ plan.elevation }}m</span>
              </div>
            </div>
            
            <div class="flex items-center justify-between">
              <div class="flex flex-wrap gap-1.5">
                 <span v-for="tag in plan.tags" :key="tag" class="text-slate-500 text-[11px] px-1.5 py-[2px] bg-slate-100 border border-slate-200/60 font-medium">
                   {{ tag }}
                 </span>
              </div>
              <div class="text-[11px] text-slate-400 font-medium whitespace-nowrap">{{ plan.date }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const mockPlans = ref([
  {
    id: 'p1',
    name: '四姑娘山大峰两日冲顶',
    distance: 15.2,
    elevation: 1320,
    tags: ['雪山体验', '交通便利', '有安全撤退点'],
    date: '2023-11-15',
    img: 'https://images.unsplash.com/photo-1522163182402-834f871fd851?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
  },
  {
    id: 'p2',
    name: '冷嘎措贡嘎倒影观景',
    distance: 10.0,
    elevation: 800,
    tags: ['贡嘎倒影', '轻松徒步', '摄影推荐'],
    date: '2023-10-02',
    img: 'https://images.unsplash.com/photo-1549887552-cb1071d3e5ca?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80'
  }
])
</script>
