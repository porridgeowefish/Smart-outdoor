<template>
  <div class="relative h-full w-full overflow-hidden bg-gradient-to-br from-emerald-50 via-slate-50 to-sky-50" style="border-radius: inherit">
    <svg class="absolute inset-0 h-full w-full" viewBox="0 0 100 64" preserveAspectRatio="xMidYMid meet">
      <path
        v-if="previewPath"
        :d="previewPath"
        class="fill-none stroke-white"
        stroke-width="6"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <path
        v-if="previewPath"
        :d="previewPath"
        class="fill-none stroke-emerald-500"
        stroke-width="3"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <path
        v-else
        d="M 10 48 C 24 22 38 50 52 30 S 74 12 90 26"
        class="fill-none stroke-emerald-500"
        stroke-width="3"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <circle v-if="startPoint" :cx="startPoint[0]" :cy="startPoint[1]" r="3.2" fill="#10b981" stroke="#fff" stroke-width="1.5" />
      <circle v-if="endPoint" :cx="endPoint[0]" :cy="endPoint[1]" r="3.2" fill="#ef4444" stroke="#fff" stroke-width="1.5" />
    </svg>

    <div v-if="showStats" class="absolute bottom-2 left-2 rounded-full bg-white/90 px-2 py-1 text-[11px] font-black text-slate-700 shadow-sm">
      {{ distanceLabel }} · +{{ elevationLabel }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { extractLineCoordinates } from '../utils/routeTrack'

const props = defineProps<{
  trackPreview?: { geojson?: unknown } | null
  distanceKm?: number
  elevationGainM?: number
  showStats?: boolean
}>()

const svgPoints = computed(() => {
  const coordinates = extractLineCoordinates(props.trackPreview?.geojson)
  if (coordinates.length < 2) return []

  const lons = coordinates.map((point) => point[0])
  const lats = coordinates.map((point) => point[1])
  const minLon = Math.min(...lons)
  const maxLon = Math.max(...lons)
  const minLat = Math.min(...lats)
  const maxLat = Math.max(...lats)
  const lonRange = Math.max(maxLon - minLon, 0.000001)
  const latRange = Math.max(maxLat - minLat, 0.000001)

  return coordinates.map((point) => {
    const x = 8 + ((point[0] - minLon) / lonRange) * 84
    const y = 56 - ((point[1] - minLat) / latRange) * 48
    return [Number(x.toFixed(2)), Number(y.toFixed(2))]
  })
})

const previewPath = computed(() => {
  if (svgPoints.value.length < 2) return ''
  return svgPoints.value
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point[0]} ${point[1]}`)
    .join(' ')
})

const startPoint = computed(() => svgPoints.value[0] || null)
const endPoint = computed(() => svgPoints.value[svgPoints.value.length - 1] || null)

const distanceLabel = computed(() => {
  if (typeof props.distanceKm !== 'number') return '-- km'
  return `${props.distanceKm.toFixed(props.distanceKm >= 10 ? 1 : 2)} km`
})

const elevationLabel = computed(() => {
  if (typeof props.elevationGainM !== 'number') return '-- m'
  return `${Math.round(props.elevationGainM)} m`
})
</script>
