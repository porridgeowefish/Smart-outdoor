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
      <div class="flex items-center gap-2">
        <button class="rounded-full bg-slate-100 px-3 py-1.5 text-[12px] font-bold text-slate-600" @click="showHistory = true">
          历史
        </button>
        <button class="rounded-full bg-emerald-50 px-3 py-1.5 text-[12px] font-bold text-emerald-600" @click="startNewChat">
          新对话
        </button>
      </div>
    </header>

    <div v-if="showHistory" class="absolute inset-0 z-40 bg-slate-900/40" @click="showHistory = false">
      <aside class="h-full w-[82%] max-w-[320px] overflow-y-auto bg-white p-4 shadow-2xl" @click.stop>
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-[16px] font-black text-slate-900">历史对话</h2>
          <button class="rounded-full bg-slate-100 px-3 py-1.5 text-[12px] font-bold text-slate-500" @click="showHistory = false">关闭</button>
        </div>
        <div v-if="historyLoading" class="py-8 text-center text-[13px] text-slate-500">正在加载...</div>
        <div v-else-if="historyItems.length === 0" class="py-8 text-center text-[13px] leading-relaxed text-slate-500">
          暂无历史对话
        </div>
        <button
          v-for="item in historyItems"
          :key="item.trip_plan_id"
          class="mb-2 w-full rounded-xl border border-slate-100 bg-slate-50 p-3 text-left active:bg-slate-100"
          @click="loadConversation(item.trip_plan_id)"
        >
          <div class="line-clamp-1 text-[14px] font-bold text-slate-800">{{ item.title }}</div>
          <div class="mt-1 line-clamp-2 text-[12px] leading-relaxed text-slate-500">{{ item.context_summary || '暂无摘要' }}</div>
          <div class="mt-2 text-[11px] font-medium text-slate-400">{{ formatDate(item.updated_at) }}</div>
        </button>
      </aside>
    </div>

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
              <div class="relative flex h-[112px] items-center justify-center overflow-hidden bg-slate-100">
                <img v-if="candidate.route.cover_image_url" :src="candidate.route.cover_image_url" class="h-full w-full object-cover" alt="" />
                <div v-else class="relative h-full w-full bg-gradient-to-br from-emerald-50 via-slate-100 to-orange-50">
                  <svg class="absolute inset-0 h-full w-full" viewBox="0 0 270 112" preserveAspectRatio="none" fill="none">
                    <path d="M18 82 C58 42 78 88 116 52 S175 26 218 56 S244 74 256 36" stroke="#10b981" stroke-width="5" stroke-linecap="round" />
                    <path d="M18 82 C58 42 78 88 116 52 S175 26 218 56 S244 74 256 36" stroke="white" stroke-width="2" stroke-linecap="round" stroke-dasharray="8 8" opacity="0.8" />
                    <circle cx="18" cy="82" r="5" fill="#2563eb" stroke="white" stroke-width="2" />
                    <circle cx="256" cy="36" r="5" fill="#ef4444" stroke="white" stroke-width="2" />
                  </svg>
                  <div class="absolute bottom-2 left-2 rounded-full bg-white/85 px-2 py-1 text-[11px] font-black text-slate-600 shadow-sm">
                    {{ formatNumber(candidate.route.distance_km, 1) }} km · +{{ formatNumber(candidate.route.elevation_gain_m, 0) }} m
                  </div>
                </div>
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
      <section class="max-h-[86vh] w-full overflow-y-auto rounded-t-[28px] bg-white p-5 shadow-2xl" @click.stop>
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

        <section class="mb-4 rounded-2xl bg-emerald-50 p-4 text-[13px] leading-relaxed text-emerald-900">
          <div class="mb-1 text-[12px] font-black text-emerald-600">AI 详情总结</div>
          <p class="whitespace-pre-wrap font-medium">{{ llmDetailCard(candidateDetail) || candidateDetail.recommendation_reason }}</p>
        </section>

        <div class="space-y-3 text-[13px] text-slate-600">
          <EvidencePanel title="规划说明" tone="slate">
            <template #badge>{{ planningDuration(candidateDetail) }}</template>
            <p class="leading-relaxed">{{ planningSummary(candidateDetail) }}</p>
          </EvidencePanel>

          <EvidencePanel title="天气证据" tone="sky">
            <template #badge>{{ statusLabel(weatherEvidence(candidateDetail).status) }}</template>
            <p class="leading-relaxed">{{ textOrFallback(weatherEvidence(candidateDetail).summary) }}</p>
            <div v-if="weatherCurrent(candidateDetail)" class="mt-2 flex flex-wrap gap-2 text-[12px] text-slate-500">
              <span>{{ weatherCurrent(candidateDetail)?.text }}</span>
              <span v-if="weatherCurrent(candidateDetail)?.temp !== undefined">{{ weatherCurrent(candidateDetail)?.temp }}°C</span>
              <span v-if="weatherCurrent(candidateDetail)?.wind_scale">风力 {{ weatherCurrent(candidateDetail)?.wind_scale }}</span>
            </div>
          </EvidencePanel>

          <EvidencePanel title="交通方案" tone="indigo">
            <template #badge>{{ statusLabel(transportEvidence(candidateDetail).status) }}</template>
            <p class="leading-relaxed">{{ textOrFallback(transportEvidence(candidateDetail).summary) }}</p>
            <div v-if="transportPlans(candidateDetail).length" class="mt-2 space-y-2">
              <div v-for="plan in transportPlans(candidateDetail).slice(0, 2)" :key="`${plan.mode}-${plan.duration_minutes}`" class="rounded-xl bg-white p-2">
                <div class="mb-1 flex items-center justify-between">
                  <span class="font-bold text-slate-700">{{ planModeLabel(plan.mode) }}</span>
                  <span class="text-[11px] text-slate-400">{{ plan.duration_minutes ? `${plan.duration_minutes} 分钟` : '耗时未确认' }}</span>
                </div>
                <div class="flex flex-wrap gap-1.5">
                  <span v-for="line in transportLines(plan).slice(0, 4)" :key="line" class="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">{{ line }}</span>
                </div>
                <ol v-if="plan.steps?.length" class="mt-2 space-y-1 text-[12px] text-slate-500">
                  <li v-for="step in plan.steps.slice(0, 3)" :key="`${step.type}-${step.line_name}-${step.instruction}`">
                    {{ stepTypeLabel(step.type) }} · {{ step.line_name || step.instruction }}
                  </li>
                </ol>
              </div>
            </div>
          </EvidencePanel>

          <EvidencePanel title="近期公开信息" tone="amber">
            <template #badge>{{ statusLabel(webEvidence(candidateDetail).status) }}</template>
            <p class="leading-relaxed">{{ textOrFallback(webEvidence(candidateDetail).summary) }}</p>
            <a
              v-for="source in webSources(candidateDetail).slice(0, 3)"
              :key="source.url"
              :href="source.url"
              target="_blank"
              rel="noreferrer"
              class="mt-2 block rounded-xl bg-white p-2 text-[12px] font-medium text-slate-700"
            >
              <span class="line-clamp-1">{{ source.title }}</span>
              <span class="line-clamp-1 text-[11px] font-normal text-slate-400">{{ source.url }}</span>
            </a>
          </EvidencePanel>
        </div>

        <div class="mt-5">
          <button
            class="w-full rounded-2xl bg-emerald-500 px-4 py-3 text-[15px] font-black text-white shadow-sm disabled:bg-slate-300"
            :disabled="isSavingCandidate"
            @click="saveCurrentCandidate"
          >
            {{ isSavingCandidate ? '保存中...' : '保存到我的规划' }}
          </button>
          <p v-if="saveMessage" class="mt-2 text-center text-[12px] font-medium text-slate-500">{{ saveMessage }}</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getCandidateRouteDetail,
  getTripPlanConversation,
  listTripPlans,
  saveCandidateRoute,
  sendTripPlanMessage,
  type CandidateRouteDetailResponse,
  type CandidateRouteItem,
  type TripPlanListItem,
} from '../api'

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  status?: 'thinking' | 'done'
  candidates?: CandidateRouteItem[]
}

type AnyRecord = Record<string, any>

const EvidencePanel = defineComponent({
  props: {
    title: { type: String, required: true },
    tone: { type: String, default: 'slate' },
  },
  setup(props, { slots }) {
    const toneClass = computed(() => {
      const map: Record<string, string> = {
        slate: 'border-slate-100 bg-white',
        sky: 'border-sky-100 bg-sky-50/60',
        indigo: 'border-indigo-100 bg-indigo-50/50',
        amber: 'border-amber-100 bg-amber-50/60',
      }
      return map[props.tone] || map.slate
    })
    return () => h('section', { class: `rounded-2xl border p-3 shadow-sm ${toneClass.value}` }, [
      h('div', { class: 'mb-1 flex items-center justify-between' }, [
        h('span', { class: 'font-black text-slate-800' }, props.title),
        h('span', { class: 'rounded-full bg-white px-2 py-0.5 text-[11px] font-bold text-slate-500' }, slots.badge?.()),
      ]),
      slots.default?.(),
    ])
  },
})

const routeQuery = useRoute()
const router = useRouter()
const inputText = ref('')
const isReplying = ref(false)
const chatContainer = ref<HTMLElement | null>(null)
const messages = ref<ChatMessage[]>([])
const tripPlanId = ref<string | null>(null)
const candidateDetail = ref<CandidateRouteDetailResponse | null>(null)
const isSavingCandidate = ref(false)
const saveMessage = ref('')
const showHistory = ref(false)
const historyLoading = ref(false)
const historyItems = ref<TripPlanListItem[]>([])

onMounted(async () => {
  await loadHistory()
  if (routeQuery.query.seed) {
    sendText(String(routeQuery.query.seed))
    router.replace('/chat')
    return
  }
  const activeTripPlanId = localStorage.getItem('active_trip_plan_id')
  if (activeTripPlanId) {
    await loadConversation(activeTripPlanId, false)
  }
})

async function sendText(text: string) {
  const content = text.trim()
  if (!content || isReplying.value) return

  messages.value.push({ id: `user-${Date.now()}`, role: 'user', content })
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
    const response = await sendTripPlanMessage({ content, trip_plan_id: tripPlanId.value })
    tripPlanId.value = response.trip_plan_id
    localStorage.setItem('active_trip_plan_id', response.trip_plan_id)
    const assistant = messages.value.find((item) => item.id === assistantId)
    if (assistant) {
      assistant.content = response.assistant_message.content
      assistant.status = 'done'
      assistant.candidates = response.candidate_routes
    }
    await loadHistory()
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
  saveMessage.value = ''
  localStorage.removeItem('active_trip_plan_id')
}

async function loadHistory() {
  historyLoading.value = true
  try {
    const response = await listTripPlans()
    historyItems.value = response.items
  } catch {
    historyItems.value = []
  } finally {
    historyLoading.value = false
  }
}

async function loadConversation(id: string, closeHistory = true) {
  try {
    const response = await getTripPlanConversation(id)
    tripPlanId.value = response.trip_plan_id
    localStorage.setItem('active_trip_plan_id', response.trip_plan_id)
    messages.value = response.messages.map((message) => ({
      id: message.id,
      role: message.role,
      content: message.content,
      status: 'done',
    }))
    if (response.candidate_routes.length) {
      const lastAssistant = [...messages.value].reverse().find((message) => message.role === 'assistant')
      if (lastAssistant) lastAssistant.candidates = response.candidate_routes
    }
    candidateDetail.value = null
    saveMessage.value = ''
    if (closeHistory) showHistory.value = false
    await scrollToBottom()
  } catch (error) {
    if (closeHistory) showHistory.value = false
    messages.value = [{
      id: `load-error-${Date.now()}`,
      role: 'assistant',
      content: error instanceof Error ? error.message : '获取对话记录失败',
      status: 'done',
    }]
  }
}

async function openCandidate(candidate: CandidateRouteItem) {
  if (!tripPlanId.value) return
  saveMessage.value = ''
  candidateDetail.value = await getCandidateRouteDetail(tripPlanId.value, candidate.candidate_id)
}

async function saveCurrentCandidate() {
  if (!tripPlanId.value || !candidateDetail.value || isSavingCandidate.value) return
  isSavingCandidate.value = true
  saveMessage.value = ''
  try {
    const snapshot = await saveCandidateRoute(tripPlanId.value, candidateDetail.value.candidate_id)
    saveMessage.value = '已保存到我的规划'
    router.push(`/plans/${snapshot.snapshot_id}`)
  } catch (error) {
    saveMessage.value = error instanceof Error ? error.message : '保存规划失败'
  } finally {
    isSavingCandidate.value = false
  }
}

async function scrollToBottom() {
  await nextTick()
  chatContainer.value?.scrollTo({ top: chatContainer.value.scrollHeight, behavior: 'smooth' })
}

function formatNumber(value: number, digits: number) {
  return value.toFixed(digits)
}

function formatDate(value: string) {
  return value.slice(0, 10)
}

function planning(candidate: CandidateRouteDetailResponse | null): AnyRecord {
  return (candidate?.planning_detail || {}) as AnyRecord
}

function evidence(candidate: CandidateRouteDetailResponse | null): AnyRecord {
  return (candidate?.evidence || {}) as AnyRecord
}

function llmDetailCard(candidate: CandidateRouteDetailResponse | null) {
  return textOrFallback(planning(candidate).llm_detail_card, '')
}

function planningSummary(candidate: CandidateRouteDetailResponse | null) {
  return textOrFallback(planning(candidate).summary)
}

function planningDuration(candidate: CandidateRouteDetailResponse | null) {
  return textOrFallback(planning(candidate).estimated_duration, '耗时未估算')
}

function weatherEvidence(candidate: CandidateRouteDetailResponse | null): AnyRecord {
  return (evidence(candidate).weather || {}) as AnyRecord
}

function weatherCurrent(candidate: CandidateRouteDetailResponse | null): AnyRecord | null {
  return (weatherEvidence(candidate).current || null) as AnyRecord | null
}

function transportEvidence(candidate: CandidateRouteDetailResponse | null): AnyRecord {
  return (evidence(candidate).transport || {}) as AnyRecord
}

function transportPlans(candidate: CandidateRouteDetailResponse | null): AnyRecord[] {
  const plans = transportEvidence(candidate).plans
  return Array.isArray(plans) ? plans : []
}

function webEvidence(candidate: CandidateRouteDetailResponse | null): AnyRecord {
  return (evidence(candidate).web_evidence || {}) as AnyRecord
}

function webSources(candidate: CandidateRouteDetailResponse | null): AnyRecord[] {
  const sources = webEvidence(candidate).sources
  return Array.isArray(sources) ? sources : []
}

function textOrFallback(value: unknown, fallback = '未确认') {
  return typeof value === 'string' && value.trim() ? value : fallback
}

function statusLabel(value: unknown) {
  const map: Record<string, string> = {
    confirmed: '已确认',
    mocked: '模拟',
    limited: '有限证据',
    unconfirmed: '未确认',
    unavailable: '不可用',
  }
  return map[String(value || '')] || '未确认'
}

function planModeLabel(mode: unknown) {
  const map: Record<string, string> = {
    self_drive: '自驾',
    public_transport: '公共交通',
    bus: '大巴',
    rail_plus_car: '高铁/城际 + 接驳',
    flight_plus_car: '飞机 + 接驳',
  }
  return map[String(mode || '')] || '交通方案'
}

function stepTypeLabel(type: unknown) {
  const map: Record<string, string> = {
    drive: '驾车',
    subway: '地铁',
    bus: '公交',
    railway: '铁路',
    walk: '步行',
    flight: '航班',
  }
  return map[String(type || '')] || '步骤'
}

function transportLines(plan: AnyRecord) {
  return [...(Array.isArray(plan.railway_lines) ? plan.railway_lines : []), ...(Array.isArray(plan.bus_lines) ? plan.bus_lines : [])]
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
