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

          <div
            v-if="message.runStatus || message.missingFields?.length || message.confirmedContext?.items?.length"
            class="space-y-2 rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-sm"
          >
            <div v-if="message.runStatus" class="flex items-center justify-between gap-3">
              <span class="text-[12px] font-black text-slate-500">状态</span>
              <span
                class="rounded-full px-2.5 py-1 text-[12px] font-black"
                :class="runStatusTone(message.runStatus)"
              >
                {{ runStatusLabel(message.runStatus) }}
              </span>
            </div>
            <div v-if="message.confirmedContext?.items?.length" class="flex max-w-full flex-wrap gap-1.5">
              <span
                v-for="item in message.confirmedContext.items"
                :key="`${message.id}-${item.field}`"
                class="rounded-lg bg-emerald-50 px-2.5 py-1 text-[12px] font-bold text-emerald-800"
              >
                {{ item.label }}：{{ item.value }}
              </span>
            </div>
            <div v-if="message.missingFields?.length" class="flex max-w-full flex-wrap gap-1.5">
              <span
                v-for="field in message.missingFields"
                :key="`${message.id}-missing-${field}`"
                class="rounded-lg bg-amber-50 px-2.5 py-1 text-[12px] font-bold text-amber-800"
              >
                待确认：{{ missingFieldLabel(field) }}
              </span>
            </div>
          </div>

          <section
            v-if="message.choiceRequest"
            class="w-full max-w-[360px] rounded-2xl border border-slate-200 bg-white p-3 shadow-sm"
          >
            <div class="mb-3 flex items-center justify-between gap-3">
              <div>
                <p class="text-[11px] font-black uppercase text-emerald-600">需要确认</p>
                <h3 class="mt-0.5 text-[15px] font-black text-slate-900">{{ activeQuestion(message)?.header }}</h3>
              </div>
              <span class="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-bold text-slate-500">
                {{ (message.activeQuestionIndex ?? 0) + 1 }}/{{ message.choiceRequest.questions.length }}
              </span>
            </div>

            <div v-if="activeQuestion(message)" class="space-y-3">
              <p class="text-[14px] font-semibold leading-relaxed text-slate-700">{{ activeQuestion(message)?.question }}</p>

              <div v-if="activeQuestion(message)?.type !== 'text'" class="grid gap-2">
                <button
                  v-for="option in activeQuestion(message)?.options"
                  :key="`${message.id}-${activeQuestion(message)?.field}-${option.value}`"
                  type="button"
                  class="choice-option"
                  :class="{ 'choice-option-active': isOptionSelected(message, activeQuestion(message)!, option.value) }"
                  :disabled="message.isSubmittingChoice"
                  @click="selectChoiceOption(message, activeQuestion(message)!, option)"
                >
                  <span class="choice-option-mark"></span>
                  <span class="min-w-0 flex-1">
                    <span class="block text-[14px] font-black leading-snug text-slate-800">{{ option.label }}</span>
                    <span v-if="option.description" class="mt-0.5 block text-[12px] font-medium leading-snug text-slate-500">{{ option.description }}</span>
                  </span>
                </button>
              </div>

              <div v-if="activeQuestion(message)?.allow_custom" class="flex gap-2">
                <input
                  v-model="message.customInputs![activeQuestion(message)!.field]"
                  class="min-w-0 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[14px] font-medium text-slate-700 outline-none focus:border-emerald-500"
                  :placeholder="activeQuestion(message)?.type === 'text' ? '填写你的答案' : '其它 / 补充信息'"
                  :disabled="message.isSubmittingChoice"
                  @keydown.enter.prevent="submitCustomChoice(message, activeQuestion(message)!)"
                />
                <button
                  type="button"
                  class="rounded-xl bg-slate-900 px-3 py-2 text-[13px] font-black text-white disabled:bg-slate-300"
                  :disabled="message.isSubmittingChoice || !message.customInputs![activeQuestion(message)!.field]?.trim()"
                  @click="submitCustomChoice(message, activeQuestion(message)!)"
                >
                  {{ isLastChoiceQuestion(message) ? '提交' : '继续' }}
                </button>
              </div>

              <div class="flex items-center justify-between">
                <button
                  type="button"
                  class="rounded-lg px-2 py-1 text-[12px] font-bold text-slate-400 disabled:opacity-0"
                  :disabled="(message.activeQuestionIndex ?? 0) === 0 || message.isSubmittingChoice"
                  @click="message.activeQuestionIndex = Math.max((message.activeQuestionIndex ?? 0) - 1, 0)"
                >
                  上一步
                </button>
                <button
                  v-if="activeQuestion(message)?.type !== 'text'"
                  type="button"
                  class="rounded-lg bg-emerald-500 px-3 py-1.5 text-[12px] font-black text-white disabled:bg-slate-300"
                  :disabled="message.isSubmittingChoice || !hasQuestionAnswer(message, activeQuestion(message)!)"
                  @click="advanceOrSubmitChoice(message)"
                >
                  {{ isLastChoiceQuestion(message) ? '提交选择' : '下一题' }}
                </button>
              </div>

              <p v-if="message.choiceError" class="rounded-lg bg-rose-50 px-3 py-2 text-[12px] font-bold text-rose-600">
                {{ message.choiceError }}
              </p>
            </div>
          </section>

          <div v-if="message.candidates?.length" class="-mx-4 flex gap-3 overflow-x-auto px-4 pb-3">
            <button
              v-for="candidate in message.candidates"
              :key="candidate.candidate_id"
              class="w-[270px] shrink-0 overflow-hidden rounded-2xl border border-slate-200 bg-white text-left shadow-sm transition-transform active:scale-[0.98]"
              @click="openCandidate(candidate)"
            >
              <div class="relative flex h-[112px] items-center justify-center overflow-hidden bg-slate-100">
                <RoutePreviewCard
                  :cover-image-url="candidate.route.cover_image_url"
                  :track-preview="candidate.route.track_preview"
                  :distance-km="candidate.route.distance_km"
                  :elevation-gain-m="candidate.route.elevation_gain_m"
                  show-stats
                />
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
            class="mb-2 w-full rounded-2xl border border-emerald-200 bg-white px-4 py-3 text-[15px] font-black text-emerald-700 shadow-sm"
            @click="openRouteDetail"
          >
            查看轨迹详情
          </button>
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
  submitTripPlanChoiceResults,
  type CandidateRouteDetailResponse,
  type CandidateRouteItem,
  type ChoiceAnswer,
  type ChoiceOption,
  type ChoiceQuestion,
  type ChoiceRequest,
  type ConfirmedContext,
  type TripPlanListItem,
} from '../api'
import RoutePreviewCard from '../components/RoutePreviewCard.vue'

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  content_type?: 'text' | 'choice_request' | 'choice_result'
  payload?: AnyRecord | null
  status?: 'thinking' | 'done'
  runStatus?: string
  candidates?: CandidateRouteItem[]
  choiceRequest?: ChoiceRequest | null
  confirmedContext?: ConfirmedContext
  missingFields?: string[]
  activeQuestionIndex?: number
  selectedAnswers?: Record<string, string | string[]>
  selectedLabels?: Record<string, string | string[]>
  customInputs?: Record<string, string>
  isSubmittingChoice?: boolean
  choiceError?: string
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
  } else if (!sessionStorage.getItem('chat_auto_routed') && historyItems.value.length === 0) {
    sessionStorage.setItem('chat_auto_routed', '1')
    router.replace('/routes')
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
    content: '正在提交给后端处理...',
    status: 'thinking',
    runStatus: 'running',
  })
  await scrollToBottom()

  try {
    const response = await sendTripPlanMessage({ content, trip_plan_id: tripPlanId.value })
    tripPlanId.value = response.trip_plan_id
    localStorage.setItem('active_trip_plan_id', response.trip_plan_id)
    const assistant = messages.value.find((item) => item.id === assistantId)
    if (assistant) {
      assistant.content = response.assistant_message.content
      assistant.content_type = response.assistant_message.content_type
      assistant.payload = response.assistant_message.payload as AnyRecord | null
      assistant.status = 'done'
      assistant.runStatus = response.run_status
      assistant.candidates = response.candidate_routes
      assistant.choiceRequest = normalizeChoiceRequest(response.choice_request) || choiceRequestFromPayload(assistant.payload)
      assistant.confirmedContext = normalizeConfirmedContext(response.confirmed_context)
      assistant.missingFields = response.missing_fields || []
      prepareChoiceState(assistant)
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
    const activeChoiceRequestId = activeChoiceRequestIdFromMessages(response.messages)
    messages.value = response.messages.map((message) => ({
      id: message.id,
      role: message.role,
      content: message.content,
      content_type: message.content_type,
      payload: message.payload as AnyRecord | null,
      choiceRequest: message.content_type === 'choice_request'
        && choiceRequestFromPayload(message.payload as AnyRecord | null)?.choice_request_id === activeChoiceRequestId
        ? choiceRequestFromPayload(message.payload as AnyRecord | null)
        : null,
      runStatus: message.content_type === 'choice_request' ? 'waiting_user' : undefined,
      status: 'done',
    })).map((message) => {
      prepareChoiceState(message)
      return message
    })
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

function normalizeChoiceRequest(value: unknown): ChoiceRequest | null {
  if (!value || typeof value !== 'object') return null
  const request = value as ChoiceRequest
  if (!request.choice_request_id || !Array.isArray(request.questions) || request.questions.length === 0) {
    return null
  }
  return request
}

function normalizeConfirmedContext(value: unknown): ConfirmedContext {
  if (!value || typeof value !== 'object') return { items: [] }
  const context = value as ConfirmedContext
  return { items: Array.isArray(context.items) ? context.items : [] }
}

function choiceRequestFromPayload(payload: AnyRecord | null | undefined): ChoiceRequest | null {
  return normalizeChoiceRequest(payload?.input)
}

function activeChoiceRequestIdFromMessages(rawMessages: Array<{ content_type?: string; payload?: unknown }>) {
  let activeId: string | null = null
  rawMessages.forEach((message) => {
    const payload = message.payload as AnyRecord | null
    if (message.content_type === 'choice_request') {
      activeId = choiceRequestFromPayload(payload)?.choice_request_id || null
    }
    if (message.content_type === 'choice_result' && payload?.choice_request_id === activeId) {
      activeId = null
    }
  })
  return activeId
}

function prepareChoiceState(message: ChatMessage) {
  if (!message.choiceRequest) return
  message.activeQuestionIndex ??= 0
  message.selectedAnswers ??= {}
  message.selectedLabels ??= {}
  message.customInputs ??= {}
  message.choiceError = ''
}

function activeQuestion(message: ChatMessage): ChoiceQuestion | null {
  const questions = message.choiceRequest?.questions || []
  return questions[message.activeQuestionIndex ?? 0] || null
}

function isLastChoiceQuestion(message: ChatMessage) {
  return (message.activeQuestionIndex ?? 0) >= ((message.choiceRequest?.questions.length || 1) - 1)
}

function isOptionSelected(message: ChatMessage, question: ChoiceQuestion, value: string) {
  const selected = message.selectedAnswers?.[question.field]
  return Array.isArray(selected) ? selected.includes(value) : selected === value
}

function selectChoiceOption(message: ChatMessage, question: ChoiceQuestion, option: ChoiceOption) {
  prepareChoiceState(message)
  if (question.type === 'multi_choice' || question.multi_select) {
    const selected = Array.isArray(message.selectedAnswers?.[question.field])
      ? [...(message.selectedAnswers?.[question.field] as string[])]
      : []
    const labels = Array.isArray(message.selectedLabels?.[question.field])
      ? [...(message.selectedLabels?.[question.field] as string[])]
      : []
    const index = selected.indexOf(option.value)
    if (index >= 0) {
      selected.splice(index, 1)
      labels.splice(index, 1)
    } else {
      selected.push(option.value)
      labels.push(option.label)
    }
    message.selectedAnswers![question.field] = selected
    message.selectedLabels![question.field] = labels
    return
  }
  message.selectedAnswers![question.field] = option.value
  message.selectedLabels![question.field] = option.label
}

function submitCustomChoice(message: ChatMessage, question: ChoiceQuestion) {
  const value = message.customInputs?.[question.field]?.trim()
  if (!value) return
  prepareChoiceState(message)
  message.selectedAnswers![question.field] = value
  message.selectedLabels![question.field] = value
  advanceOrSubmitChoice(message)
}

function hasQuestionAnswer(message: ChatMessage, question: ChoiceQuestion) {
  const value = message.selectedAnswers?.[question.field]
  return Array.isArray(value) ? value.length > 0 : Boolean(value)
}

async function advanceOrSubmitChoice(message: ChatMessage) {
  if (!message.choiceRequest || !tripPlanId.value || message.isSubmittingChoice) return
  const question = activeQuestion(message)
  if (!question || !hasQuestionAnswer(message, question)) return
  if (!isLastChoiceQuestion(message)) {
    message.activeQuestionIndex = (message.activeQuestionIndex ?? 0) + 1
    await scrollToBottom()
    return
  }
  await submitChoiceRequest(message)
}

async function submitChoiceRequest(message: ChatMessage) {
  if (!message.choiceRequest || !tripPlanId.value) return
  const choiceRequest = message.choiceRequest
  const answers: ChoiceAnswer[] = message.choiceRequest.questions
    .filter((question) => hasQuestionAnswer(message, question))
    .map((question) => {
      const value = message.selectedAnswers![question.field]
      const label = message.selectedLabels![question.field] || value
      const customText = message.customInputs?.[question.field]?.trim()
      return {
        field: question.field,
        value,
        label,
        custom_text: customText || null,
      }
    })
  if (answers.length === 0) return

  message.isSubmittingChoice = true
  message.choiceError = ''
  message.choiceRequest = null
  const userMessageId = `choice-user-${Date.now()}`
  const assistantId = `choice-assistant-${Date.now()}`
  messages.value.push({
    id: userMessageId,
    role: 'user',
    content: choiceSummary(answers),
    content_type: 'choice_result',
    status: 'done',
  })
  messages.value.push({
    id: assistantId,
    role: 'assistant',
    content: '正在基于已确认条件继续处理...',
    status: 'thinking',
    runStatus: 'running',
  })
  await scrollToBottom()

  try {
    const response = await submitTripPlanChoiceResults(tripPlanId.value, {
      choice_request_id: choiceRequest.choice_request_id,
      answers,
    })
    message.isSubmittingChoice = false

    const submittedUserMessage = messages.value.find((item) => item.id === userMessageId)
    if (submittedUserMessage) {
      submittedUserMessage.id = response.user_message_id
    }
    const assistant = messages.value.find((item) => item.id === assistantId)
    if (assistant) {
      assistant.id = response.assistant_message.id
      assistant.content = response.assistant_message.content
      assistant.content_type = response.assistant_message.content_type
      assistant.payload = response.assistant_message.payload as AnyRecord | null
      assistant.status = 'done'
      assistant.runStatus = response.run_status
      assistant.candidates = response.candidate_routes
      assistant.choiceRequest = normalizeChoiceRequest(response.choice_request) || choiceRequestFromPayload(response.assistant_message.payload as AnyRecord | null)
      assistant.confirmedContext = normalizeConfirmedContext(response.confirmed_context)
      assistant.missingFields = response.missing_fields || []
      prepareChoiceState(assistant)
    }
    await loadHistory()
    await scrollToBottom()
  } catch (error) {
    const assistant = messages.value.find((item) => item.id === assistantId)
    if (assistant) {
      assistant.content = error instanceof Error ? error.message : '提交选择失败'
      assistant.status = 'done'
      assistant.runStatus = 'failed'
    }
    message.choiceRequest = choiceRequest
    prepareChoiceState(message)
    message.choiceError = error instanceof Error ? error.message : '提交选择失败'
    message.isSubmittingChoice = false
  }
}

function choiceSummary(answers: ChoiceAnswer[]) {
  return `选择：${answers.map((answer) => {
    if (answer.custom_text) return answer.custom_text
    return Array.isArray(answer.label) ? answer.label.join('、') : answer.label
  }).join('；')}`
}

function runStatusLabel(status: string) {
  const map: Record<string, string> = {
    running: '后端处理中',
    waiting_user: '等待继续确认',
    succeeded: '已返回结果',
    failed: '处理失败',
  }
  return map[status] || status
}

function runStatusTone(status: string) {
  const map: Record<string, string> = {
    running: 'bg-sky-50 text-sky-700',
    waiting_user: 'bg-amber-50 text-amber-700',
    succeeded: 'bg-emerald-50 text-emerald-700',
    failed: 'bg-rose-50 text-rose-700',
  }
  return map[status] || 'bg-slate-100 text-slate-600'
}

function missingFieldLabel(field: string) {
  const map: Record<string, string> = {
    activity_goal: '目标',
    departure_area: '出发地',
    time_window: '时间',
    transport_hint: '交通',
    terrain_tolerance: '路况接受度',
    safety_priority: '安全优先级',
    preference_tags: '偏好',
    avoid_tags: '避开项',
    scenery_preferences: '风景偏好',
    supply_requirement: '补给要求',
    ability_hint: '强度偏好',
  }
  return map[field] || field
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

function openRouteDetail() {
  if (!candidateDetail.value) return
  router.push(`/routes/${candidateDetail.value.route.route_id}`)
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

.choice-option {
  display: flex;
  width: 100%;
  align-items: flex-start;
  gap: 0.75rem;
  border: 1px solid rgb(226 232 240);
  border-radius: 0.875rem;
  background: rgb(248 250 252);
  padding: 0.75rem;
  text-align: left;
  transition: border-color 140ms ease, background-color 140ms ease, box-shadow 140ms ease, transform 140ms ease;
}

.choice-option:active {
  transform: scale(0.99);
}

.choice-option:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.choice-option-active {
  border-color: rgb(16 185 129);
  background: rgb(236 253 245);
  box-shadow: 0 0 0 2px rgb(16 185 129 / 0.12);
}

.choice-option-mark {
  margin-top: 0.125rem;
  display: flex;
  height: 1.125rem;
  width: 1.125rem;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  border: 2px solid rgb(148 163 184);
  background: white;
}

.choice-option-active .choice-option-mark {
  border-color: rgb(16 185 129);
  background: rgb(16 185 129);
}

.choice-option-active .choice-option-mark::after {
  content: "";
  height: 0.375rem;
  width: 0.375rem;
  border-radius: 9999px;
  background: white;
}
</style>
