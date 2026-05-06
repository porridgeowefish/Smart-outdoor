<template>
  <div class="flex h-[100dvh] flex-col overflow-hidden bg-[#f4f5f7] pb-[60px] font-sans">
    <header class="sticky top-0 z-20 flex h-14 shrink-0 items-center border-b border-slate-100 bg-white px-4 shadow-sm">
      <h1 class="flex-1 text-center text-[18px] font-bold text-slate-800">个人主页</h1>
      <button class="absolute right-4 text-sm font-semibold text-slate-500 hover:text-slate-900" @click="logout">
        登出
      </button>
    </header>

    <main class="flex-1 overflow-y-auto pb-8">
      <div v-if="loading" class="flex h-[60vh] items-center justify-center">
        <span class="h-8 w-8 animate-spin rounded-full border-[3px] border-slate-200 border-t-emerald-500"></span>
      </div>

      <div v-else-if="user" class="space-y-6">
        <section class="flex items-center gap-4 border-b border-slate-100 bg-white px-5 py-6 shadow-sm">
          <button
            class="group relative flex h-[72px] w-[72px] shrink-0 items-center justify-center overflow-hidden rounded-full border-[3px] border-emerald-50 bg-emerald-100 text-3xl font-bold text-emerald-600 shadow-inner"
            @click="triggerAvatarUpload"
          >
            <img v-if="user.avatar_url" :src="user.avatar_url" class="h-full w-full object-cover" alt="avatar" />
            <span v-else>{{ userInitial }}</span>
            <span class="absolute inset-0 flex items-center justify-center bg-black/40 text-xs font-bold text-white opacity-0 transition-opacity group-hover:opacity-100">
              更换
            </span>
          </button>
          <input ref="fileInput" class="hidden" type="file" accept="image/*" @change="onAvatarChange" />

          <div class="min-w-0 flex-1">
            <div class="mb-1 flex items-center gap-2">
              <h2 class="truncate text-[20px] font-black tracking-tight text-slate-900">
                {{ user.nickname || '未设置昵称' }}
              </h2>
              <button class="flex h-7 w-7 items-center justify-center rounded-full bg-slate-50 text-slate-400 hover:bg-emerald-50 hover:text-emerald-600" @click="startEdit">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
                  <path d="m15 5 4 4" />
                </svg>
              </button>
            </div>
            <p class="text-[13px] font-medium tracking-wide text-slate-400">ID: {{ user.username }}</p>
          </div>
        </section>

        <section class="space-y-4 px-4">
          <div class="ml-1 flex items-center justify-between">
            <h3 class="text-[16px] font-bold tracking-wide text-slate-800">运动能力评估</h3>
            <span v-if="abilityProfile" class="rounded-full bg-slate-200 px-2 py-1 text-[11px] font-bold text-slate-600">
              {{ confidenceLabel(abilityProfile.confidence) }}
            </span>
          </div>

          <div v-if="abilityProfile" class="overflow-hidden rounded-[24px] border border-slate-100 bg-white p-5 shadow-sm">
            <div class="mb-5 flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <div class="mb-1 text-[11px] font-bold uppercase tracking-wider text-slate-400">综合评级</div>
                <div class="text-[20px] font-black uppercase leading-none tracking-tight text-slate-800">
                  {{ levelLabel(abilityProfile.level) }}
                </div>
              </div>
              <div class="text-right">
                <div class="mb-1 text-[11px] font-bold uppercase tracking-wider text-slate-400">分析基数</div>
                <div class="rounded-lg border border-slate-100 bg-slate-50 px-2.5 py-1 text-[15px] font-black text-slate-700">
                  {{ abilityProfile.activity_count }} <span class="text-[11px] font-medium text-slate-400">条轨迹</span>
                </div>
              </div>
            </div>

            <div class="space-y-6">
              <score-block
                title="耐力评分"
                color="blue"
                :score="abilityProfile.endurance_score"
                :metrics="[
                  { label: '最大等效距离', value: metric('recent_max_effort_km'), unit: 'km' },
                  { label: '耐力容量', value: metric('endurance_capacity_effort_km'), unit: 'effort km' },
                ]"
              />

              <score-block
                title="爬升评分"
                color="orange"
                :score="abilityProfile.climb_score"
                :metrics="[
                  { label: '5 分钟峰值 VAM', value: metric('best_vam_5min_m_per_h'), unit: 'm/h' },
                  { label: '20 分钟峰值 VAM', value: metric('best_vam_20min_m_per_h'), unit: 'm/h' },
                  { label: '60 分钟峰值 VAM', value: metric('best_vam_60min_m_per_h'), unit: 'm/h' },
                  { label: '平均爬升速率', value: metric('avg_climb_speed_m_per_min'), unit: 'm/min' },
                ]"
              />
            </div>

            <p class="mt-5 rounded-[16px] bg-slate-50 p-3 text-[12px] font-medium leading-relaxed text-slate-500">
              {{ abilityMessage }}
            </p>
          </div>

          <div v-else class="rounded-[24px] border border-slate-100 bg-white p-8 text-center shadow-sm">
            <div class="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-slate-50 text-slate-400">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="m8 3 4 8 5-5 5 15H2L8 3z" />
              </svg>
            </div>
            <h3 class="mb-2 text-[18px] font-bold text-slate-800">暂无能力画像</h3>
            <p class="text-[13px] font-medium leading-relaxed text-slate-500">上传完成过的户外轨迹后，会自动生成耐力和爬升能力评估。</p>
          </div>
        </section>

        <section class="mt-6 px-4">
          <div class="mb-5 ml-1 flex items-center justify-between pr-1">
            <h3 class="flex items-center gap-2 text-[16px] font-bold tracking-wide text-slate-800">
              已完成轨迹
              <span class="rounded bg-slate-200 px-1.5 py-0.5 text-[10px] font-black text-slate-600">{{ tracks.length }}</span>
            </h3>
            <button
              class="flex items-center gap-1.5 rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-1.5 text-[13px] font-black text-emerald-600 transition-colors active:bg-emerald-100 disabled:opacity-60"
              :disabled="uploading"
              @click="triggerTrackUpload"
            >
              <svg v-if="!uploading" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" x2="12" y1="3" y2="15" />
              </svg>
              <span v-else class="h-3 w-3 animate-spin rounded-full border-[2px] border-emerald-200 border-t-emerald-600"></span>
              {{ uploading ? '正在解析' : '导入轨迹' }}
            </button>
          </div>

          <input ref="trackInput" class="hidden" type="file" accept=".kml,.gpx,.geojson" @change="onTrackUpload" />

          <div v-if="activityGroups.length > 0" class="space-y-8">
            <div v-for="group in activityGroups" :key="group.month">
              <div class="mb-3 flex items-end justify-between rounded-[16px] border border-slate-100 bg-white p-3 shadow-sm">
                <div>
                  <div class="mb-0.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">月度统计</div>
                  <h3 class="text-[18px] font-black tracking-tight text-slate-800">{{ group.month }} 月</h3>
                </div>
                <div class="text-right">
                  <div class="mb-1 flex items-baseline justify-end gap-1 text-[20px] font-black leading-none tracking-tight text-emerald-600">
                    {{ formatTotalDistance(group.tracks) }} <span class="text-[11px] font-bold uppercase tracking-widest text-emerald-400">km</span>
                  </div>
                  <div class="text-[11px] font-bold text-slate-400">{{ group.tracks.length }} 次运动 · {{ formatTotalHours(group.tracks) }}</div>
                </div>
              </div>

              <div class="space-y-3">
                <article v-for="track in group.tracks" :key="track.id" class="rounded-[20px] border border-slate-100 bg-white p-4 shadow-sm">
                  <div class="mb-2 flex items-start justify-between gap-3">
                    <div class="flex items-baseline gap-1 text-[22px] font-black tracking-tight text-slate-800">
                      {{ formatNumber(track.distance_km, 2) }}
                      <span class="text-[11px] font-bold uppercase tracking-widest text-slate-400">km</span>
                    </div>
                    <div class="rounded-full bg-orange-50 px-2 py-1 text-[11px] font-bold text-orange-600">
                      +{{ formatNumber(track.elevation_gain_m, 0) }} m
                    </div>
                  </div>
                  <div class="mb-1 flex items-center gap-2 text-[12px] font-bold text-slate-600">
                    <span>{{ formatTime(track.moving_time_seconds) }}</span>
                    <span class="h-1 w-1 rounded-full bg-slate-300"></span>
                    <span>{{ track.pace_or_speed }}</span>
                  </div>
                  <div class="text-[11px] font-medium text-slate-400">
                    {{ formatDate(track.activity_date) }} · {{ displayLocation(track.location) }}
                  </div>
                </article>
              </div>
            </div>
          </div>

          <div v-else class="mt-4 rounded-[20px] border border-slate-100 bg-white p-6 text-center shadow-sm">
            <p class="text-[13px] font-medium text-slate-500">还没有上传任何完成轨迹。</p>
          </div>
        </section>
      </div>

      <div v-else class="flex h-[60vh] flex-col items-center justify-center p-6 text-center">
        <p class="mb-6 text-[14px] text-slate-500">未能加载用户信息</p>
        <button class="rounded-[16px] bg-slate-900 px-8 py-3 text-[14px] font-bold text-white shadow-md" @click="logout">重新登录</button>
      </div>
    </main>

    <div v-if="editing" class="absolute inset-0 z-50 flex items-end bg-slate-900/50 backdrop-blur-sm" @click="editing = false">
      <div class="w-full rounded-t-[32px] bg-white pb-8 pt-2 shadow-[0_-10px_40px_rgba(0,0,0,0.1)]" @click.stop>
        <div class="mx-auto mb-5 mt-2 h-1.5 w-12 rounded-full bg-slate-200"></div>
        <div class="px-6">
          <h3 class="mb-6 text-[22px] font-black tracking-tight text-slate-800">修改资料</h3>
          <label class="mb-2 block text-[12px] font-bold uppercase tracking-wide text-slate-400">展示昵称</label>
          <input
            v-model="editForm.nickname"
            class="mb-5 w-full rounded-[16px] border border-slate-200 bg-slate-50 px-5 py-4 text-[16px] font-bold text-slate-900 shadow-inner outline-none transition-colors focus:border-emerald-500 focus:bg-emerald-50/30"
            type="text"
            placeholder="设置你的展示昵称"
          />
          <div v-if="error" class="mb-5 rounded-[16px] border border-red-100 bg-red-50 p-4 text-[13px] font-bold text-red-600">
            {{ error }}
          </div>
          <div class="flex gap-4">
            <button class="w-[120px] shrink-0 rounded-[20px] bg-slate-100 py-4 text-[16px] font-bold text-slate-600" @click="editing = false">取消</button>
            <button class="flex flex-1 items-center justify-center gap-2 rounded-[20px] bg-emerald-500 py-4 text-[16px] font-bold text-white shadow-[0_8px_20px_rgba(16,185,129,0.25)] disabled:opacity-70" :disabled="updating" @click="updateProfile">
              <span v-if="updating" class="h-5 w-5 animate-spin rounded-full border-[3px] border-emerald-300 border-t-white"></span>
              {{ updating ? '保存中' : '保存修改' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  apiFetch,
  clearAuthToken,
  getAbilityProfile,
  getMe,
  listActivityTracks,
  uploadActivityTrack,
  type AbilityProfileResponse,
  type ActivityTrackItem,
  type UserPublic,
} from '../api'

type Metric = {
  label: string
  value: number | null
  unit: string
}

const ScoreBlock = defineComponent({
  name: 'ScoreBlock',
  props: {
    title: { type: String, required: true },
    color: { type: String, required: true },
    score: { type: Number, default: null },
    metrics: { type: Array<Metric>, required: true },
  },
  setup(props) {
    return () => {
      const score = typeof props.score === 'number' ? props.score : 0
      const colorClass = props.color === 'orange' ? 'from-orange-400 to-red-500' : 'from-blue-400 to-indigo-500'
      const dotClass = props.color === 'orange' ? 'bg-orange-500' : 'bg-blue-500'

      return h('div', [
        h('div', { class: 'mb-2.5 flex items-end justify-between' }, [
          h('div', { class: 'flex items-center gap-2' }, [
            h('div', { class: `h-3.5 w-1 rounded-full ${dotClass}` }),
            h('span', { class: 'text-[14px] font-bold text-slate-700' }, props.title),
          ]),
          h('div', { class: 'flex items-baseline gap-1' }, [
            h('span', { class: 'font-mono text-[28px] font-black leading-none text-slate-800' }, Math.round(score * 100)),
            h('span', { class: 'text-[13px] font-bold text-slate-400' }, '/100'),
          ]),
        ]),
        h('div', { class: 'mb-4 h-2 w-full overflow-hidden rounded-full bg-[#f4f5f7] shadow-inner' }, [
          h('div', { class: `h-full rounded-full bg-gradient-to-r ${colorClass}`, style: { width: `${Math.max(0, Math.min(100, score * 100))}%` } }),
        ]),
        h('div', { class: 'grid grid-cols-2 gap-2 rounded-[16px] border border-slate-100 bg-[#f8f9fc] p-3' },
          props.metrics.map((item) =>
            h('div', { class: 'min-w-0 pl-2' }, [
              h('div', { class: 'mb-1.5 truncate text-[11px] font-bold text-slate-500' }, item.label),
              h('div', { class: 'flex items-baseline gap-1' }, [
                h('span', { class: 'font-mono text-[18px] font-black tracking-tight text-slate-800' }, item.value === null ? '--' : formatNumber(item.value, item.unit === 'km' ? 1 : 0)),
                h('span', { class: 'text-[11px] font-bold text-slate-400' }, item.unit),
              ]),
            ]),
          ),
        ),
      ])
    }
  },
})

const router = useRouter()
const loading = ref(true)
const updating = ref(false)
const uploading = ref(false)
const error = ref('')
const user = ref<UserPublic | null>(null)
const abilityProfile = ref<AbilityProfileResponse | null>(null)
const tracks = ref<ActivityTrackItem[]>([])
const editing = ref(false)

const trackInput = ref<HTMLInputElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const editForm = reactive({
  nickname: '',
})

onMounted(async () => {
  await fetchProfile()
  if (user.value) await fetchTracks()
})

const userInitial = computed(() => {
  const name = user.value?.nickname || user.value?.username || 'U'
  return name.charAt(0).toUpperCase()
})

const activityGroups = computed(() => {
  const groups: Record<string, ActivityTrackItem[]> = {}
  tracks.value.forEach((track) => {
    if (!groups[track.month]) groups[track.month] = []
    groups[track.month].push(track)
  })
  return Object.keys(groups).map((month) => ({ month, tracks: groups[month] }))
})

const abilityMessage = computed(() => {
  if (!abilityProfile.value) return ''
  return `当前能力画像基于 ${abilityProfile.value.activity_count} 条完成活动轨迹生成，可信度为${confidenceText(abilityProfile.value.confidence)}。`
})

async function fetchProfile() {
  if (!localStorage.getItem('access_token')) {
    loading.value = false
    router.replace('/login')
    return
  }

  try {
    user.value = await getMe()
    abilityProfile.value = await getAbilityProfile()
  } catch (err) {
    console.error(err)
    clearAuthToken()
    router.replace('/login')
  } finally {
    loading.value = false
  }
}

async function fetchTracks() {
  try {
    const data = await listActivityTracks()
    tracks.value = data.tracks || []
  } catch (err) {
    console.error(err)
  }
}

function metric(key: string): number | null {
  const value = abilityProfile.value?.metrics_json?.[key]
  return typeof value === 'number' ? value : null
}

function triggerAvatarUpload() {
  fileInput.value?.click()
}

async function onAvatarChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await apiFetch('/api/me/avatar', { method: 'POST', body: formData })
    if (!res.ok) throw new Error('头像上传失败')
    user.value = await res.json()
  } catch (err) {
    console.error(err)
  } finally {
    if (fileInput.value) fileInput.value.value = ''
  }
}

function triggerTrackUpload() {
  trackInput.value?.click()
}

async function onTrackUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    uploading.value = true
    const data = await uploadActivityTrack({ file })
    abilityProfile.value = data.ability_profile
    await fetchTracks()
  } catch (err) {
    console.error(err)
  } finally {
    uploading.value = false
    if (trackInput.value) trackInput.value.value = ''
  }
}

function startEdit() {
  editForm.nickname = user.value?.nickname || ''
  editing.value = true
  error.value = ''
}

async function updateProfile() {
  updating.value = true
  error.value = ''

  try {
    const nickname = editForm.nickname.trim()
    const res = await apiFetch('/api/me', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nickname }),
    })
    if (!res.ok) throw new Error('保存失败')
    user.value = await res.json()
    editing.value = false
  } catch (err) {
    error.value = err instanceof Error ? err.message : '网络错误'
  } finally {
    updating.value = false
  }
}

function logout() {
  clearAuthToken()
  router.replace('/login')
}

function formatNumber(value: number | null | undefined, digits = 1) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '--'
  return value.toFixed(digits)
}

function formatTotalDistance(groupTracks: ActivityTrackItem[]) {
  return formatNumber(groupTracks.reduce((sum, item) => sum + item.distance_km, 0), 2)
}

function formatTotalHours(groupTracks: ActivityTrackItem[]) {
  const totalSeconds = groupTracks.reduce((sum, item) => sum + (item.moving_time_seconds || 0), 0)
  return `${(totalSeconds / 3600).toFixed(1)} 小时`
}

function formatTime(seconds: number | null) {
  if (!seconds) return '--'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  if (Number.isNaN(date.getTime())) return dateStr
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

function displayLocation(location: string) {
  if (!location || location === 'unknown' || location === '待识别') {
    return '位置待识别'
  }
  return location
}

function levelLabel(level: string) {
  const map: Record<string, string> = {
    unknown: '未知',
    beginner: '初级',
    normal: '进阶',
    strong: '强者',
  }
  return map[level] || level
}

function confidenceLabel(confidence: string) {
  const map: Record<string, string> = {
    unknown: '可信度未知',
    low: '低可信度',
    medium: '中可信度',
    high: '高可信度',
  }
  return map[confidence] || confidence
}

function confidenceText(confidence: string) {
  const map: Record<string, string> = {
    unknown: '未知',
    low: '低',
    medium: '中',
    high: '高',
  }
  return map[confidence] || confidence
}
</script>
