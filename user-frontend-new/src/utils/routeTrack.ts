/**
 * 轨迹渲染工具：从 GeoJSON 提取坐标、转换坐标系、按海拔或坡度着色。
 *
 * 核心功能：
 * - extractLineCoordinates: 从各种 GeoJSON 结构中提取坐标点
 * - toAmapPath: WGS84 坐标转为高德 GCJ02 坐标
 * - buildElevationColoredGroups: 按相对海拔分级着色（绿→红 = 低→高）
 * - buildSlopeColoredGroups: 按坡度分级着色（暂保留，待坡度算法优化后切回）
 */

import { haversineMeters, wgs84ToGcj02, type TrackCoordinate } from './geo'

/** 带颜色的轨迹线段组，用于高德地图 Polyline 渲染 */
export type ColoredTrackGroup = {
  color: string
  path: [number, number][]  // GCJ02 坐标对
}

/**
 * 坡度分级颜色：绿(平缓) → 黄(中等) → 橙(较陡) → 红(陡峭)
 * 0-5% 绿色, 5-10% 黄绿, 10-18% 黄色, 18-28% 橙色, 28%+ 红色
 */
const SLOPE_COLORS = [
  '#22c55e',  // < 5%  平缓
  '#84cc16',  // 5-10%
  '#eab308',  // 10-18%
  '#f97316',  // 18-28%
  '#ef4444',  // > 28% 陡峭
]

const ELEVATION_COLORS = [
  '#22c55e',
  '#84cc16',
  '#eab308',
  '#f97316',
  '#ef4444',
]

/**
 * 从 GeoJSON 中递归提取所有 LineString 坐标点。
 * 支持 Feature、FeatureCollection、GeometryCollection、MultiLineString 等嵌套结构。
 */
export function extractLineCoordinates(geojson: unknown): TrackCoordinate[] {
  if (!geojson || typeof geojson !== 'object') return []
  const geometry = geojson as Record<string, unknown>
  if (geometry.type === 'LineString' && Array.isArray(geometry.coordinates)) {
    return geometry.coordinates
      .filter(isCoordinate)
      .map((item) => item as TrackCoordinate)
  }
  if (geometry.type === 'MultiLineString' && Array.isArray(geometry.coordinates)) {
    return geometry.coordinates
      .flatMap((line) => Array.isArray(line) ? line : [])
      .filter(isCoordinate)
      .map((item) => item as TrackCoordinate)
  }
  if (geometry.type === 'Feature' && geometry.geometry) {
    return extractLineCoordinates(geometry.geometry)
  }
  if (geometry.type === 'FeatureCollection' && Array.isArray(geometry.features)) {
    return geometry.features.flatMap((feature) => extractLineCoordinates(feature))
  }
  if (geometry.type === 'GeometryCollection' && Array.isArray(geometry.geometries)) {
    return geometry.geometries.flatMap((item) => extractLineCoordinates(item))
  }
  return []
}

/** 将 WGS84 坐标点数组转换为高德地图 GCJ02 坐标，过滤无效坐标 */
export function toAmapPath(points: TrackCoordinate[], coordinateSystem: string): [number, number][] {
  return points
    .filter((point) => Number.isFinite(point[0]) && Number.isFinite(point[1]))
    .map((point) => {
      const lon = point[0]
      const lat = point[1]
      return coordinateSystem.toLowerCase() === 'wgs84' ? wgs84ToGcj02(lon, lat) : [lon, lat]
    })
}

/**
 * 按坡度将轨迹分段着色，返回相邻同色合并后的线段组。
 * 每段包含颜色和对应的 GCJ02 坐标路径，直接用于高德地图 AMap.Polyline 渲染。
 */
export function buildSlopeColoredGroups(points: TrackCoordinate[], coordinateSystem: string): ColoredTrackGroup[] {
  if (points.length < 2) return []
  const amapPath = toAmapPath(points, coordinateSystem)
  if (amapPath.length < 2) return []
  // 无海拔数据时统一使用绿色
  const hasElevationData = points.some((point) => typeof point[2] === 'number')
  if (!hasElevationData) return [{ color: SLOPE_COLORS[0], path: amapPath }]

  const groups: ColoredTrackGroup[] = []
  let current: ColoredTrackGroup | null = null

  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1]
    const next = points[index]
    const color = slopeColor(previous, next)
    const segmentStart = amapPath[index - 1]
    const segmentEnd = amapPath[index]

    // 相邻段颜色相同则合并（减少 Polyline 数量提升渲染性能）
    if (!current || current.color !== color) {
      current = { color, path: [segmentStart, segmentEnd] }
      groups.push(current)
    } else {
      current.path.push(segmentEnd)
    }
  }

  return groups
}

/**
 * 按相对海拔将轨迹分段着色。
 * 使用当前轨迹自己的最低/最高海拔做归一化，低海拔为绿色，高海拔逐步过渡到红色。
 */
export function buildElevationColoredGroups(points: TrackCoordinate[], coordinateSystem: string): ColoredTrackGroup[] {
  if (points.length < 2) return []
  const amapPath = toAmapPath(points, coordinateSystem)
  if (amapPath.length < 2) return []

  const elevations = points
    .map((point) => point[2])
    .filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
  if (elevations.length < 2) return [{ color: ELEVATION_COLORS[0], path: amapPath }]

  const minElevation = Math.min(...elevations)
  const maxElevation = Math.max(...elevations)
  const elevationRange = maxElevation - minElevation
  if (elevationRange <= 0) return [{ color: ELEVATION_COLORS[0], path: amapPath }]

  const groups: ColoredTrackGroup[] = []
  let current: ColoredTrackGroup | null = null

  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1]
    const next = points[index]
    const color = elevationColor(previous, next, minElevation, elevationRange)
    const segmentStart = amapPath[index - 1]
    const segmentEnd = amapPath[index]

    if (!current || current.color !== color) {
      current = { color, path: [segmentStart, segmentEnd] }
      groups.push(current)
    } else {
      current.path.push(segmentEnd)
    }
  }

  return groups
}

/** 检查轨迹点中是否包含海拔数据 */
export function hasElevation(points: TrackCoordinate[]) {
  return points.some((point) => typeof point[2] === 'number')
}

/** 根据两点间坡度（高程差/水平距离）返回对应颜色 */
function slopeColor(previous: TrackCoordinate, next: TrackCoordinate) {
  if (typeof previous[2] !== 'number' || typeof next[2] !== 'number') {
    return SLOPE_COLORS[0]
  }
  const distance = haversineMeters(previous, next)
  if (distance < 1) return SLOPE_COLORS[0]  // 距离太短忽略坡度
  const grade = Math.abs(next[2] - previous[2]) / distance
  if (grade < 0.05) return SLOPE_COLORS[0]
  if (grade < 0.10) return SLOPE_COLORS[1]
  if (grade < 0.18) return SLOPE_COLORS[2]
  if (grade < 0.28) return SLOPE_COLORS[3]
  return SLOPE_COLORS[4]
}

function elevationColor(
  previous: TrackCoordinate,
  next: TrackCoordinate,
  minElevation: number,
  elevationRange: number,
) {
  if (typeof previous[2] !== 'number' || typeof next[2] !== 'number') {
    return ELEVATION_COLORS[0]
  }
  const segmentElevation = (previous[2] + next[2]) / 2
  const ratio = Math.min(1, Math.max(0, (segmentElevation - minElevation) / elevationRange))
  const colorIndex = Math.min(
    ELEVATION_COLORS.length - 1,
    Math.floor(ratio * ELEVATION_COLORS.length),
  )
  return ELEVATION_COLORS[colorIndex]
}

/** 类型守卫：判断值是否为合法的坐标数组 [number, number] */
function isCoordinate(value: unknown): value is number[] {
  return Array.isArray(value)
    && value.length >= 2
    && typeof value[0] === 'number'
    && typeof value[1] === 'number'
}
