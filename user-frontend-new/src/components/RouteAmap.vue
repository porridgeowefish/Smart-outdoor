<template>
  <div class="relative w-full h-full bg-slate-200">
    <div ref="container" class="w-full h-full"></div>
    <div v-if="statusMessage" class="absolute inset-0 bg-slate-900/55 text-white flex items-center justify-center text-[13px] px-6 text-center">
      {{ statusMessage }}
    </div>
    <div v-else-if="!elevationAvailable" class="absolute left-3 bottom-3 bg-white/90 backdrop-blur text-slate-600 text-[11px] px-2 py-1 rounded-full shadow">
      无坡度数据，使用单色轨迹
    </div>
    <div v-else class="absolute left-3 bottom-3 bg-white/90 backdrop-blur rounded-full shadow px-2 py-1 flex items-center gap-1.5">
      <span class="text-[10px] text-slate-500 font-medium">坡度</span>
      <span class="w-16 h-1.5 rounded-full bg-gradient-to-r from-[#22c55e] via-[#eab308] to-[#ef4444]"></span>
    </div>
    <div v-if="mapReady" class="absolute right-3 bottom-3 bg-white/95 backdrop-blur rounded-full shadow p-1 flex items-center gap-1">
      <button
        v-for="option in layerOptions"
        :key="option.value"
        @click="setLayerMode(option.value)"
        :class="layerMode === option.value ? 'bg-emerald-500 text-white' : 'text-slate-600'"
        class="px-2.5 py-1 text-[11px] font-bold rounded-full transition-colors"
      >
        {{ option.label }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import AMapLoader from '@amap/amap-jsapi-loader'
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { buildSlopeColoredGroups, extractLineCoordinates, hasElevation, toAmapPath } from '../utils/routeTrack'

const props = defineProps<{
  geojson: unknown
  coordinateSystem?: string
}>()

const container = ref<HTMLDivElement | null>(null)
const statusMessage = ref('')
const elevationAvailable = ref(true)
const mapReady = ref(false)
const layerMode = ref<'standard' | 'satellite' | 'satelliteRoad'>('standard')

const layerOptions = [
  { value: 'standard' as const, label: '标准' },
  { value: 'satellite' as const, label: '卫星' },
  { value: 'satelliteRoad' as const, label: '卫星路网' },
]

let map: any = null
let AMap: any = null
let overlays: any[] = []
let baseLayers: Record<string, any[]> = {}

onMounted(initMap)
onUnmounted(() => {
  clearOverlays()
  map?.destroy()
  map = null
  mapReady.value = false
})

watch(
  () => props.geojson,
  () => {
    if (map && AMap) drawTrack()
  },
  { deep: true },
)

async function initMap() {
  const key = import.meta.env.VITE_AMAP_JS_KEY
  if (!key) {
    statusMessage.value = '缺少 VITE_AMAP_JS_KEY，无法加载高德地图'
    return
  }

  const securityJsCode = import.meta.env.VITE_AMAP_SECURITY_JS_CODE
  if (securityJsCode) {
    window._AMapSecurityConfig = { securityJsCode }
  }

  try {
    AMap = await AMapLoader.load({
      key,
      version: '2.0',
      plugins: ['AMap.Scale'],
    })
    if (!container.value) return
    baseLayers = createBaseLayers()
    map = new AMap.Map(container.value, {
      viewMode: '2D',
      zoom: 11,
      resizeEnable: true,
      layers: baseLayers.standard,
    })
    map.addControl(new AMap.Scale())
    mapReady.value = true
    drawTrack()
  } catch (e: any) {
    statusMessage.value = e?.message || '高德地图加载失败'
  }
}

function drawTrack() {
  clearOverlays()
  statusMessage.value = ''

  const points = extractLineCoordinates(props.geojson)
  if (points.length < 2) {
    statusMessage.value = '没有可渲染的轨迹数据'
    return
  }

  const coordinateSystem = props.coordinateSystem || 'wgs84'
  elevationAvailable.value = hasElevation(points)
  const groups = buildSlopeColoredGroups(points, coordinateSystem)
  if (groups.length === 0) {
    statusMessage.value = '轨迹坐标无效，无法渲染'
    return
  }
  overlays = groups.map((group) => new AMap.Polyline({
    path: group.path.map((point) => new AMap.LngLat(point[0], point[1])),
    strokeColor: group.color,
    strokeOpacity: 0.95,
    strokeWeight: 6,
    lineJoin: 'round',
    lineCap: 'round',
    showDir: true,
    zIndex: 80,
  }))

  const fullPath = toAmapPath(points, coordinateSystem)
  if (fullPath.length < 2) {
    statusMessage.value = '轨迹坐标无效，无法渲染'
    return
  }
  const startMarker = new AMap.Marker({
    position: new AMap.LngLat(fullPath[0][0], fullPath[0][1]),
    content: markerContent('起', '#10b981'),
    offset: new AMap.Pixel(-12, -12),
    zIndex: 100,
  })
  const endMarker = new AMap.Marker({
    position: new AMap.LngLat(fullPath[fullPath.length - 1][0], fullPath[fullPath.length - 1][1]),
    content: markerContent('终', '#ef4444'),
    offset: new AMap.Pixel(-12, -12),
    zIndex: 100,
  })

  overlays.push(startMarker, endMarker)
  map.add(overlays)
  map.setFitView(overlays, false, [48, 36, 48, 36])
}

function createBaseLayers() {
  return {
    standard: [AMap.createDefaultLayer()],
    satellite: [new AMap.TileLayer.Satellite()],
    satelliteRoad: [new AMap.TileLayer.Satellite(), new AMap.TileLayer.RoadNet()],
  }
}

function setLayerMode(mode: 'standard' | 'satellite' | 'satelliteRoad') {
  layerMode.value = mode
  if (!map) return
  map.setLayers(baseLayers[mode])
  if (overlays.length > 0) {
    map.add(overlays)
  }
}

function clearOverlays() {
  if (map && overlays.length > 0) {
    map.remove(overlays)
  }
  overlays = []
}

function markerContent(text: string, color: string) {
  return `<div style="width:24px;height:24px;border-radius:999px;background:${color};color:white;border:2px solid white;box-shadow:0 2px 8px rgba(15,23,42,.25);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;">${text}</div>`
}
</script>
