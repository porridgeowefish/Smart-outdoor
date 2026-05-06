/**
 * 坐标转换工具：WGS84 → GCJ02（国测局坐标系）。
 *
 * 高德地图使用 GCJ02 坐标系，而后端存储的轨迹坐标为 WGS84。
 * 在渲染到高德地图之前需要进行坐标偏移转换。
 * 中国境外坐标不做偏移，直接返回原值。
 */

/** 轨迹坐标：[经度, 纬度] 或 [经度, 纬度, 海拔] */
export type TrackCoordinate = [number, number] | [number, number, number]

const PI = Math.PI
const A = 6378245.0  // 长半轴（克拉索夫斯基椭球体）
const EE = 0.00669342162296594323  // 第一偏心率平方

/**
 * WGS84 坐标转 GCJ02 坐标（火星坐标系）。
 * 中国境外坐标不做偏移（高德地图对境外使用 WGS84）。
 */
export function wgs84ToGcj02(lon: number, lat: number): [number, number] {
  if (outOfChina(lon, lat)) return [lon, lat]

  let dLat = transformLat(lon - 105.0, lat - 35.0)
  let dLon = transformLon(lon - 105.0, lat - 35.0)
  const radLat = lat / 180.0 * PI
  let magic = Math.sin(radLat)
  magic = 1 - EE * magic * magic
  const sqrtMagic = Math.sqrt(magic)
  dLat = (dLat * 180.0) / ((A * (1 - EE)) / (magic * sqrtMagic) * PI)
  dLon = (dLon * 180.0) / (A / sqrtMagic * Math.cos(radLat) * PI)
  return [lon + dLon, lat + dLat]
}

/** 使用半正矢公式（Haversine）计算两个坐标点之间的距离（米） */
export function haversineMeters(a: TrackCoordinate, b: TrackCoordinate): number {
  const earthRadiusMeters = 6371008.8
  const lat1 = degreesToRadians(a[1])
  const lat2 = degreesToRadians(b[1])
  const dLat = degreesToRadians(b[1] - a[1])
  const dLon = degreesToRadians(b[0] - a[0])
  const x = Math.sin(dLat / 2) ** 2
    + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2
  return earthRadiusMeters * 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1 - x))
}

function degreesToRadians(value: number) {
  return value * PI / 180
}

/** 判断坐标是否在中国境外（粗略边界） */
function outOfChina(lon: number, lat: number) {
  return lon < 72.004 || lon > 137.8347 || lat < 0.8293 || lat > 55.8271
}

/** GCJ02 纬度偏移量计算 */
function transformLat(x: number, y: number) {
  let ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y
    + 0.2 * Math.sqrt(Math.abs(x))
  ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0
  ret += (20.0 * Math.sin(y * PI) + 40.0 * Math.sin(y / 3.0 * PI)) * 2.0 / 3.0
  ret += (160.0 * Math.sin(y / 12.0 * PI) + 320 * Math.sin(y * PI / 30.0)) * 2.0 / 3.0
  return ret
}

/** GCJ02 经度偏移量计算 */
function transformLon(x: number, y: number) {
  let ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y
    + 0.1 * Math.sqrt(Math.abs(x))
  ret += (20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0 / 3.0
  ret += (20.0 * Math.sin(x * PI) + 40.0 * Math.sin(x / 3.0 * PI)) * 2.0 / 3.0
  ret += (150.0 * Math.sin(x / 12.0 * PI) + 300.0 * Math.sin(x / 30.0 * PI)) * 2.0 / 3.0
  return ret
}
