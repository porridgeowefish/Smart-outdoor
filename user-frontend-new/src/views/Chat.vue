<template>
  <div class="relative flex h-full flex-col overflow-hidden bg-slate-50">
    <header class="z-10 flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 shadow-sm">
      <div class="flex items-center gap-2">
        <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500 text-white">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M3 20L12 4L21 20H3Z" />
          </svg>
        </div>
        <h1 class="text-[16px] font-bold text-slate-800">出去走走</h1>
      </div>
      <button class="rounded-full bg-emerald-50 px-3 py-1.5 text-[12px] font-bold text-emerald-600" @click="startNewChat">
        新对话
      </button>
    </header>

    <main ref="chatContainer" class="flex flex-1 flex-col gap-5 overflow-y-auto p-4">
      <section v-if="messages.length === 0" class="flex h-full flex-col items-center justify-center gap-4 text-center">
        <div class="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 shadow-inner">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z" />
          </svg>
        </div>
        <div>
          <h2 class="mb-2 text-[20px] font-bold text-slate-800">告诉我这次想怎么走</h2>
          <p class="text-[14px] text-slate-500">我会根据线路库、强度和证据约束先给你 3 条候选。</p>
        </div>
        <div class="mt-4 flex flex-wrap justify-center gap-2 px-4">
          <button class="quick-btn" @click="sendText('周末想从成都出发看雪山')">周末从成都看雪山</button>
          <button class="quick-btn" @click="sendText('成都周边自驾一日徒步，中等强度')">自驾一日中等强度</button>
          <button class="quick-btn" @click="sendText('想找一条轻松徒步路线')">轻松徒步路线</button>
        </div>
      </section>

      <article v-for="message in messages" :key="message.id" class="flex flex-col">
        <div v-if="message.role === 'user'" class="max-w-[85%] self-end rounded-2xl rounded-tr-sm bg-emerald-500 px-4 py-3 text-white shadow-sm">
          <p class="break-words text-[15px] leading-relaxed">{{ message.content }}</p>
        </div>

        <div v-else class="flex max-w-[94%] flex-col gap-3 self-start">
          <div class="flex items-end gap-2">
            <div class="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M3 20L12 4L21 20H3Z" />
              </svg>
            </div>
            <span class="text-[12px] font-medium text-slate-500">户外助手</span>
          </div>

          <div class="rounded-2xl rounded-tl-sm border border-slate-100 bg-white px-4 py-3 text-slate-800 shadow-sm">
            <p class="whitespace-pre-wrap break-words text-[15px] leading-relaxed">{{ message.content }}</p>
            <div v-if="message.status === 'thinking'" class="mt-3 flex gap-1">
              <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-emerald-400"></span>
              <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-emerald-400 [animation-delay:150ms]"></span>
              <span class="h-1.5 w-1.5 animate-bounce rounded-full bg-emerald-400 [animation-delay:300ms]"></span>
            </div>
          </div>

          <div v-if="message.candidates?.length" class="-mx-4 flex gap-3 overflow-x-auto px-4 pb-3">
            <button
              v-for="candidate in message.candidates"
              :key="candidate.candidate_id"
              class="w-[270px] shrink-0 overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition-transform active:scale-[0.98]"
              @click="openCandidate(candidate)"
            >
              <div class="flex h-[112px] items-center justify-center bg-slate-100">
                <img v-if="candidate.route.cover_image_url" :src="candidate.route.cover_image_url" class="h-full w-full object-cover" alt="" />
                <div v-else class="px-4 text-center text-[12px] font-bold text-slate-400">{{ candidate.route.location }}</div>
              </div>
              <div class="p-4">
                <div class="mb-1.5 flex items-start justify-between gap-2">
                  <h3 class="line-clamp-2 text-[16px] font-bold leading-snug text-slate-800">{{ candidate.route.name }}</h3>
                  <span class="shrink-0 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-black text-emerald-600">#{{ candidate.rank }}</span>
                </div>
                <p class="mb-2 text-[12px] font-medium text-slate-400">{{ candidate.route.location }}</p>
                <div class="mb-3 flex gap-3 text-[13px] font-medium text-slate-500">
                  <span>{{ formatNumber(candidate.route.distance_km, 1) }} km</span>
                  <span>+{{ formatNumber(candidate.route.elevation_gain_m, 0) }} m</span>
                </div>
                <div class="flex flex-wrap gap-1.5">
                  <span v-for="tag in candidate.advantage_tags" :key="tag" class="rounded-md bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700">{{ tag }}</span>
                </div>
              </div>
            </button>
          </div>
        </div>
      </article>
    </main>

    <form class="relative z-10 flex shrink-0 items-end border-t border-slate-100 bg-white p-4 shadow-[0_-4px_20px_rgba(0,0,0,0.02)]" @submit.prevent="handleSubmit">
      <textarea
        v-model="inputText"
        rows="1"
        placeholder="输入你的出发地、时间、偏好或强度要求"
        class="max-h-[120px] min-h-[46px] w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-4 pr-12 text-[15px] shadow-inner outline-none focus:border-emerald-500"
        @keydown.enter.prevent="handleSubmit"
      ></textarea>
      <button
        type="submit"
        :disabled="!inputText.trim() || isReplying"
        class="absolute bottom-5 right-5 flex h-[34px] w-[34px] items-center justify-center rounded-xl bg-emerald-500 text-white transition-colors disabled:bg-slate-300 disabled:opacity-50"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="m22 2-7 20-4-9-9-4Z" />
          <path d="M22 2 11 13" />
        </svg>
      </button>
    </form>

    <div v-if="candidateDetail" class="absolute inset-0 z-50 flex items-end bg-slate-900/50 backdrop-blur-sm" @click="candidateDetail = null">
      <section class="max-h-[82vh] w-full overflow-y-auto rounded-t-[28px] bg-white p-5 shadow-2xl" @click.stop>
        <div class="mx-auto mb-5 h-1.5 w-12 rounded-full bg-slate-200"></div>
        <div class="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 class="text-[20px] font-black text-slate-900">{{ candidateDetail.route.name }}</h2>
            <p class="mt-1 text-[13px] font-medium text-slate-400">{{ candidateDetail.route.location }}</p>
          </div>
          <button class="rounded-full bg-slate-100 px-3 py-1.5 text-[12px] font-bold text-slate-500" @click="candidateDetail = null">关闭</button>
        </div>
        <div class="mb-4 grid grid-cols-2 gap-2">
          <div class="rounded-2xl bg-slate-50 p-3">
            <div class="text-[11px] font-bold text-slate-400">距离</div>
            <div class="mt-1 text-[20px] font-black text-slate-800">{{ formatNumber(candidateDetail.route.distance_km, 1) }} km</div>
          </div>
          <div class="rounded-2xl bg-orange-50 p-3">
            <div class="text-[11px] font-bold text-orange-400">爬升</div>
            <div class="mt-1 text-[20px] font-black text-orange-600">+{{ formatNumber(candidateDetail.route.elevation_gain_m, 0) }} m</div>
          </div>
        </div>
        <p class="mb-4 rounded-2xl bg-emerald-50 p-3 text-[13px] font-medium leading-relaxed text-emerald-800">
          {{ candidateDetail.recommendation_reason }}
        </p>
        <div class="space-y-3 text-[13px] text-slate-600">
          <p><span class="font-bold text-slate-800">规划说明：</span>{{ candidateDetail.planning_detail.summary }}</p>
          <p><span class="font-bold text-slate-800">天气：</span>{{ candidateDetail.evidence.weather?.summary || '未确认' }}</p>
          <p><span class="font-bold text-slate-800">交通：</span>{{ candidateDetail.evidence.transport?.summary || '未确认' }}</p>
          <p><span class="font-bold text-slate-800">近期路况：</span>{{ candidateDetail.evidence.web_evidence?.summary || '未确认' }}</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getCandidateRouteDetail,
  sendTripPlanMessage,
  type CandidateRouteDetailResponse,
  type CandidateRouteItem,
} from '../api'

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  status?: 'thinking' | 'done'
  candidates?: CandidateRouteItem[]
}

const routeQuery = useRoute()
const router = useRouter()
const inputText = ref('')
const isReplying = ref(false)
const chatContainer = ref<HTMLElement | null>(null)
const messages = ref<ChatMessage[]>([])
const tripPlanId = ref<string | null>(null)
const candidateDetail = ref<CandidateRouteDetailResponse | null>(null)

onMounted(() => {
  if (routeQuery.query.seed) {
    sendText(String(routeQuery.query.seed))
    router.replace('/chat')
  }
})

async function sendText(text: string) {
  const content = text.trim()
  if (!content || isReplying.value) return

  messages.value.push({
    id: `user-${Date.now()}`,
    role: 'user',
    content,
  })
  inputText.value = ''
  isReplying.value = true
  await scrollToBottom()

  const assistantId = `assistant-${Date.now()}`
  messages.value.push({
    id: assistantId,
    role: 'assistant',
    content: '正在整理你的需求...',
    status: 'thinking',
  })
  await scrollToBottom()

  try {
    const response = await sendTripPlanMessage({
      content,
      trip_plan_id: tripPlanId.value,
    })
    tripPlanId.value = response.trip_plan_id
    const assistant = messages.value.find((item) => item.id === assistantId)
    if (assistant) {
      assistant.content = response.assistant_message.content
      assistant.status = 'done'
      assistant.candidates = response.candidate_routes
    }
  } catch (error) {
    const assistant = messages.value.find((item) => item.id === assistantId)
    if (assistant) {
      assistant.content = error instanceof Error ? error.message : '发送失败，请稍后再试。'
      assistant.status = 'done'
    }
  } finally {
    isReplying.value = false
    await scrollToBottom()
  }
}

function handleSubmit() {
  sendText(inputText.value)
}

function startNewChat() {
  messages.value = []
  inputText.value = ''
  tripPlanId.value = null
  candidateDetail.value = null
}

async function openCandidate(candidate: CandidateRouteItem) {
  if (!tripPlanId.value) return
  candidateDetail.value = await getCandidateRouteDetail(
    tripPlanId.value,
    candidate.candidate_id,
  )
}

async function scrollToBottom() {
  await nextTick()
  chatContainer.value?.scrollTo({
    top: chatContainer.value.scrollHeight,
    behavior: 'smooth',
  })
}

function formatNumber(value: number, digits: number) {
  return value.toFixed(digits)
}
</script>

<style scoped>
.quick-btn {
  border: 1px solid rgb(226 232 240);
  border-radius: 9999px;
  background: white;
  padding: 0.625rem 1rem;
  font-size: 13px;
  font-weight: 600;
  color: rgb(71 85 105);
  box-shadow: 0 1px 2px rgb(0 0 0 / 0.05);
}
</style>
