<template>
  <div class="flex flex-col h-[100dvh] bg-[#f8f9fa] relative overflow-hidden z-[100] absolute inset-0 font-sans">
    <!-- Header overlays on map -->
    <div class="absolute top-0 left-0 right-0 h-14 flex items-center justify-between px-4 z-20">
      <button @click="$router.back()" class="w-8 h-8 flex items-center justify-center bg-black/40 backdrop-blur-md text-white hover:bg-black/60 transition-colors border border-white/10 shadow-sm">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
      </button>
      <div class="flex justify-center items-center h-full">
        <span class="text-white font-bold tracking-widest text-[13px] drop-shadow-md uppercase">AI 路线解析</span>
      </div>
      <div class="w-8"></div>
    </div>

    <!-- Map & Track Layer -->
    <div class="w-full h-[35%] bg-slate-900 relative shrink-0">
      <img src="https://images.unsplash.com/photo-1524661135-423995f22d0b?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80" 
           class="w-full h-full object-cover opacity-60 mix-blend-overlay filter contrast-125" />
      
      <!-- Mock GPX Track SVG -->
      <svg class="absolute inset-0 w-full h-full pointer-events-none drop-shadow-lg" viewBox="0 0 400 400" preserveAspectRatio="none">
        <path d="M 50,300 C 100,280 120,350 200,250 S 280,100 350,150" 
              fill="none" stroke="#3b82f6" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
        <circle cx="50" cy="300" r="6" fill="#10b981" stroke="#ffffff" stroke-width="2" />
        <circle cx="350" cy="150" r="6" fill="#ef4444" stroke="#ffffff" stroke-width="2" />
      </svg>
      <div class="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white to-transparent"></div>
    </div>

    <!-- Scrollable Bottom Sheet -->
    <div class="flex-grow bg-white -mt-6 z-10 relative flex flex-col shadow-[0_-4px_24px_rgba(0,0,0,0.08)] overflow-y-auto pb-safe">
      <div class="p-6">
        <!-- Title and Date -->
        <h2 class="text-[22px] font-black text-slate-900 leading-tight mb-2 tracking-tight">{{ planData.name }}</h2>
        <p class="text-slate-500 text-[13px] mb-6 flex items-center gap-1.5 font-bold tracking-wide uppercase border-b border-slate-100 pb-4">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/></svg>
          计划出发日期: {{ planData.date }}
        </p>

        <!-- Route Stats Grid -->
        <div class="grid grid-cols-3 border-y border-slate-100 bg-slate-50 divide-x divide-slate-200/60 mb-6">
           <div class="p-3 text-center">
             <div class="text-[20px] font-black font-mono text-slate-800 leading-none mb-1">{{ planData.distance }}</div>
             <div class="text-[11px] font-bold text-slate-400 tracking-wider">总里程 (KM)</div>
           </div>
           <div class="p-3 text-center">
             <div class="text-[20px] font-black font-mono text-slate-800 leading-none mb-1">{{ planData.elevation }}</div>
             <div class="text-[11px] font-bold text-slate-400 tracking-wider">爬升 (M)</div>
           </div>
           <div class="p-3 text-center">
             <div class="text-[20px] font-black font-mono text-slate-800 leading-none mb-1 text-blue-600">{{ planData.duration.replace(':', 'h') }}m</div>
             <div class="text-[11px] font-bold text-slate-400 tracking-wider">预估耗时</div>
           </div>
        </div>

        <!-- Metric secondary row -->
        <div class="flex justify-between px-2 mb-8 border-b border-slate-100 pb-5">
           <div>
             <div class="text-[11px] text-slate-400 font-bold uppercase tracking-wider mb-1">海拔区间</div>
             <div class="text-[15px] font-bold text-slate-700 font-mono">{{ planData.minAltitude }} - {{ planData.maxAltitude }}m</div>
           </div>
           <div class="text-right">
             <div class="text-[11px] text-slate-400 font-bold uppercase tracking-wider mb-1">推算平均移速</div>
             <div class="text-[15px] font-bold text-slate-700 font-mono">{{ planData.avgSpeed }} km/h</div>
           </div>
        </div>

        <!-- AI Personalized Analysis (Replaces restrictive schedule) -->
        <div class="bg-indigo-50/50 border-l-4 border-indigo-500 p-4 mb-6">
          <h3 class="text-[15px] font-bold text-slate-800 mb-2 flex items-center gap-2 tracking-tight">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="text-indigo-500"><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>
            专属分析：为何推荐
          </h3>
          <p class="text-[13.5px] text-slate-700 leading-relaxed font-medium text-justify">
            {{ planData.id === 'p1' ? '基于您近期活动的高爬升速率(>12m/min)和稳定的耐力表现，四姑娘山大峰虽然具有一定挑战性，但完全处于您的安全阈值内。您的 VO₂Max 估算值表明您有能力应对 4000 米级的低氧环境。此外，该路线绝佳的高海拔风光和标志性冲顶极大地匹配了您"进阶探索者"的用户档案配置。' : '结合您近期的体能记录，冷嘎措路线单日 8.5km 的距离和约 400m 的爬升对您来说完全没有竞技压力。这是一条难度极低、视觉回报率极高的徒步线路，能让您在放松身体的同时，全身心地沉浸于贡嘎神山的雪山倒影拍摄之中。' }}
          </p>
        </div>

        <!-- Weather Forecast Data Widget -->
        <div class="bg-slate-900 p-4 mb-6 text-white relative overflow-hidden shadow-md">
          <div class="flex items-center justify-between mb-3 border-b border-white/10 pb-3">
             <div class="flex items-center gap-2 text-white/90">
                <span class="text-[13px] font-bold tracking-widest uppercase">目的地气候预测</span>
             </div>
             <!-- Mock Weather Icon -->
             <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" class="text-yellow-400 drop-shadow-sm"><path d="M12 4V2M12 22v-2M4 12H2M22 12h-2M5.636 5.636l-1.414-1.414M19.778 19.778l-1.414-1.414M5.636 18.364l-1.414 1.414M19.778 4.222l-1.414 1.414M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10Z"/></svg>
          </div>
          <div class="flex items-end justify-between">
             <div class="flex items-baseline gap-2">
               <span class="text-[28px] font-black leading-none font-mono tracking-tighter">{{ planData.id === 'p1' ? '8°' : '15°' }}</span>
               <span class="text-[13px] font-bold text-white/70">{{ planData.id === 'p1' ? '晴转多云' : '局部多云' }}</span>
             </div>
             <div class="text-right">
                <div class="text-[12px] font-bold text-white/80 mb-0.5">{{ planData.id === 'p1' ? '极强紫外线' : '强紫外线' }}</div>
                <div class="text-[12px] font-medium text-white/50">{{ planData.id === 'p1' ? '西北风 4级' : '西南风 2级' }}</div>
             </div>
          </div>
        </div>
        
        <!-- Risk dynamic logic (AI matched to conditions) -->
        <div class="border border-slate-200 p-4 mb-6 shadow-sm">
           <div class="text-slate-900 font-bold text-[14px] mb-2 flex items-center gap-2">
             <span class="w-2 h-2 bg-red-500 rounded-full"></span>
             环境风险预警
           </div>
           <p class="text-slate-600 text-[13px] leading-relaxed font-medium">该线路在最高海拔达到 {{ planData.maxAltitude }} 米，由于昼夜温差效应，{{ planData.id === 'p1' ? '夜间极易出现剧烈降温甚至达到零下。请务必携带足够的保暖图层，切忌在高海拔剧烈奔跑或饮酒。' : '部分背阴路段可能存在暗冰，行走时请保持步态稳定。' }}</p>
        </div>

        <!-- Packing List -->
        <div>
          <h3 class="text-[18px] font-black text-slate-900 mb-4 tracking-tight">定制装备清单</h3>
          <div class="flex flex-col gap-px bg-slate-100">
             <div class="flex items-start gap-3 bg-white p-3 border border-slate-200/50">
               <input type="checkbox" class="mt-1 w-4 h-4 rounded-sm border-slate-300 text-blue-600 focus:ring-blue-600 focus:ring-offset-0" />
               <div>
                  <span class="text-[14px] text-slate-800 font-bold block mb-0.5">硬壳冲锋衣 + {{ planData.id === 'p1' ? '排骨羽绒' : '抓绒内胆' }}</span>
                  <span class="text-[12px] text-slate-500 font-medium leading-normal block">用于阻挡高山阵风，灵活适应气温变化。</span>
               </div>
             </div>
             <div class="flex items-start gap-3 bg-white p-3 border border-slate-200/50">
               <input type="checkbox" checked class="mt-1 w-4 h-4 rounded-sm border-slate-300 text-blue-600 focus:ring-blue-600 focus:ring-offset-0" />
               <div>
                  <span class="text-[14px] text-slate-800 font-bold block mb-0.5">高热量路餐与保温杯(1L)</span>
                  <span class="text-[12px] text-slate-500 font-medium leading-normal block">多携带含糖较高的零食以及充足的热水。</span>
               </div>
             </div>
             <div class="flex items-start gap-3 bg-white p-3 border border-slate-200/50" v-if="planData.id === 'p1'">
               <input type="checkbox" class="mt-1 w-4 h-4 rounded-sm border-slate-300 text-blue-600 focus:ring-blue-600 focus:ring-offset-0" />
               <div>
                  <span class="text-[14px] text-slate-800 font-bold block mb-0.5">头灯及备用电池</span>
                  <span class="text-[12px] text-slate-500 font-medium leading-normal block">该路线可能涉及早晚弱光时段，必须保证独立充足照明。</span>
               </div>
             </div>
          </div>
        </div>
        
        <div class="h-8"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const planData = ref({
  id: '',
  name: '',
  date: '',
  distance: '0',
  elevation: '0',
  duration: '00:00',
  maxAltitude: '0',
  minAltitude: '0',
  avgSpeed: '0.0'
})

onMounted(() => {
  const id = route.params.id as string
  
  if (id === 'p1') {
    planData.value = {
      id,
      name: '四姑娘山大峰两日冲顶',
      date: '2023-11-15',
      distance: '18.4',
      elevation: '1355',
      duration: '09:30',
      maxAltitude: '5025',
      minAltitude: '3200',
      avgSpeed: '1.9'
    }
  } else {
    // fallback or 'p2'
    planData.value = {
      id,
      name: '冷嘎措贡嘎倒影观景',
      date: '2023-10-02',
      distance: '8.5',
      elevation: '420',
      duration: '04:15',
      maxAltitude: '4500',
      minAltitude: '3800',
      avgSpeed: '2.5'
    }
  }
})
</script>

<style scoped>
.pb-safe {
  padding-bottom: env(safe-area-inset-bottom);
}
</style>
