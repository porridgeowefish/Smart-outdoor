<template>
  <div class="flex flex-col h-full w-full bg-slate-50 relative overflow-hidden">
    <div class="flex-grow overflow-y-auto">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
    
    <nav class="flex-shrink-0 bg-white border-t border-slate-200 h-[64px] pb-safe flex">
      <router-link 
        to="/chat" 
        class="flex-1 flex flex-col items-center justify-center gap-1 text-slate-400 select-none"
        active-class="text-emerald-500"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"/></svg>
        <span class="text-[10px] font-medium">出去走走</span>
      </router-link>
      
      <router-link 
        to="/plans" 
        class="flex-1 flex flex-col items-center justify-center gap-1 text-slate-400 select-none"
        active-class="text-emerald-500"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="m16 13-3.5 3.5-2-2"/></svg>
        <span class="text-[10px] font-medium">我的规划</span>
      </router-link>
      
      <router-link 
        to="/routes" 
        class="flex-1 flex flex-col items-center justify-center gap-1 text-slate-400 select-none"
        active-class="text-emerald-500"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/></svg>
        <span class="text-[10px] font-medium">线路</span>
      </router-link>
      
      <router-link 
        to="/profile" 
        class="flex-1 flex flex-col items-center justify-center gap-1 text-slate-400 select-none"
        active-class="text-emerald-500"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        <span class="text-[10px] font-medium">个人中心</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.pb-safe {
  padding-bottom: env(safe-area-inset-bottom);
}
</style>
