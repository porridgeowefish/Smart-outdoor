/**
 * API 客户端封装。
 *
 * 基于 openapi-fetch 生成的类型安全客户端，自动从 OpenAPI schema 导入类型。
 * 所有 API 函数统一返回数据或抛出 ApiError，由调用方处理 UI 反馈。
 */

import createClient from 'openapi-fetch'
import type { paths, components } from './generated/openapi'

// 从 OpenAPI schema 导出的类型别名，供 Vue 组件直接使用
export type LoginRequest = components['schemas']['LoginRequest']
export type LoginResponse = components['schemas']['LoginResponse']
export type RegisterRequest = components['schemas']['RegisterRequest']
export type RegisterResponse = components['schemas']['RegisterResponse']
export type UserPublic = components['schemas']['UserPublic']
export type RouteListItem = components['schemas']['RouteListItem']
export type RouteListResponse = components['schemas']['RouteListResponse']
export type RouteUploadResponse = components['schemas']['RouteUploadResponse']
export type RouteDetailResponse = components['schemas']['RouteDetailResponse']
export type RouteTagTaxonomyResponse = components['schemas']['RouteTagTaxonomyResponse']
export type AbilityProfileResponse = components['schemas']['AbilityProfileResponse']
export type ActivityTrackItem = components['schemas']['ActivityTrackItem']
export type ActivityTrackListResponse = components['schemas']['ActivityTrackListResponse']
export type ActivityUploadResponse = components['schemas']['ActivityUploadResponse']
export type TripPlanMessageRequest = components['schemas']['TripPlanMessageRequest']
export type TripPlanMessagePostResponse = components['schemas']['TripPlanMessagePostResponse']
export type CandidateRouteItem = components['schemas']['CandidateRouteItem']
export type CandidateRouteDetailResponse = components['schemas']['CandidateRouteDetailResponse']
export type TripPlanListItem = components['schemas']['TripPlanListItem']
export type TripPlanListResponse = components['schemas']['TripPlanListResponse']
export type TripPlanConversationResponse = components['schemas']['TripPlanConversationResponse']
export type RoutePlanSnapshotItem = components['schemas']['RoutePlanSnapshotItem']
export type RoutePlanSnapshotListResponse = components['schemas']['RoutePlanSnapshotListResponse']
export type RoutePlanSnapshotDetailResponse = components['schemas']['RoutePlanSnapshotDetailResponse']

/** API 错误，携带 HTTP 状态码和后端返回的错误体 */
export class ApiError extends Error {
  status: number
  payload: unknown

  constructor(status: number, message: string, payload?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

/** 类型安全的 API 客户端， baseUrl 为空表示同源请求 */
export const apiClient = createClient<paths>({ baseUrl: '' })

// 请求拦截器：自动注入 localStorage 中的 JWT Token
apiClient.use({
  onRequest({ request }) {
    const token = localStorage.getItem('access_token')
    if (token && !request.headers.has('Authorization')) {
      request.headers.set('Authorization', `Bearer ${token}`)
    }
    return request
  },
})

/** 检查本地是否存在已保存的 Token（用于路由守卫判断登录状态） */
export function hasAuthToken() {
  return Boolean(localStorage.getItem('access_token'))
}

/** 清除本地存储的 Token（登出时调用） */
export function clearAuthToken() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('token_type')
}

/** 登录：成功后将 Token 存入 localStorage */
export async function login(payload: LoginRequest): Promise<LoginResponse> {
  const { data, error, response } = await apiClient.POST('/api/auth/login', {
    body: payload,
  })
  if (error || !data) throw buildApiError(response.status, error, '登录失败')
  localStorage.setItem('access_token', data.access_token)
  localStorage.setItem('token_type', data.token_type)
  return data
}

/** 注册新用户 */
export async function register(payload: RegisterRequest): Promise<RegisterResponse> {
  const { data, error, response } = await apiClient.POST('/api/auth/register', {
    body: payload,
  })
  if (error || !data) throw buildApiError(response.status, error, '注册失败')
  return data
}

/** 获取当前登录用户信息 */
export async function getMe(): Promise<UserPublic> {
  const { data, error, response } = await apiClient.GET('/api/me')
  if (error || !data) throw buildApiError(response.status, error, '获取用户信息失败')
  return data
}

/** 查询线路列表，支持关键词、可见性和分页参数 */
export async function listRoutes(params: {
  keyword?: string
  visibility?: string
  page?: number
  page_size?: number
} = {}): Promise<RouteListResponse> {
  const { data, error, response } = await apiClient.GET('/api/routes', {
    params: {
      query: {
        visibility: params.visibility ?? 'all',
        page: params.page ?? 1,
        page_size: params.page_size ?? 20,
        keyword: params.keyword || undefined,
      },
    },
  })
  if (error || !data) throw buildApiError(response.status, error, '获取线路列表失败')
  return data
}

/** 获取单条线路的完整详情 */
export async function getRouteDetail(routeId: string): Promise<RouteDetailResponse> {
  const { data, error, response } = await apiClient.GET('/api/routes/{route_id}', {
    params: {
      path: { route_id: routeId },
    },
  })
  if (error || !data) throw buildApiError(response.status, error, '获取线路详情失败')
  return data
}

/** 上传线路文件（FormData，不经过 openapi-fetch，手动处理 multipart） */
export async function getRouteTagTaxonomy(): Promise<RouteTagTaxonomyResponse> {
  const response = await fetch('/api/routes/tag-taxonomy', { headers: authHeaders() })
  const body = await parseJson(response)
  if (!response.ok) throw buildApiError(response.status, body, '????????')
  return body as RouteTagTaxonomyResponse
}

export async function uploadRoute(payload: {
  file: File
  coverImage?: File | null
  name: string
  description?: string
  visibility: 'public' | 'private'
  manualTags?: Record<string, unknown>
}): Promise<RouteUploadResponse> {
  const formData = new FormData()
  formData.append('file', payload.file)
  if (payload.coverImage) formData.append('cover_image', payload.coverImage)
  formData.append('name', payload.name)
  if (payload.description?.trim()) formData.append('description', payload.description.trim())
  formData.append('visibility', payload.visibility)
  if (payload.manualTags) formData.append('manual_tags', JSON.stringify(payload.manualTags))

  const response = await fetch('/api/routes/upload', {
    method: 'POST',
    headers: authHeaders(),
    body: formData,
  })
  const body = await parseJson(response)
  if (!response.ok) {
    throw buildApiError(response.status, body, '上传线路失败')
  }
  return body as RouteUploadResponse
}

export async function getAbilityProfile(): Promise<AbilityProfileResponse | null> {
  const { data, error, response } = await apiClient.GET('/api/me/ability-profile')
  if (response.status === 404) return null
  if (error || !data) throw buildApiError(response.status, error, '获取能力画像失败')
  return data
}

export async function listActivityTracks(): Promise<ActivityTrackListResponse> {
  const { data, error, response } = await apiClient.GET('/api/me/activity-tracks')
  if (error || !data) throw buildApiError(response.status, error, '获取运动轨迹失败')
  return data
}

export async function uploadActivityTrack(payload: {
  file: File
  activityDate?: string
  sourceType?: string
}): Promise<ActivityUploadResponse> {
  const formData = new FormData()
  formData.append('file', payload.file)
  if (payload.activityDate) formData.append('activity_date', payload.activityDate)
  formData.append('source_type', payload.sourceType ?? 'manual_upload')

  const response = await fetch('/api/me/activity-tracks/upload', {
    method: 'POST',
    headers: authHeaders(),
    body: formData,
  })
  const body = await parseJson(response)
  if (!response.ok) {
    throw buildApiError(response.status, body, '上传运动轨迹失败')
  }
  return body as ActivityUploadResponse
}

export async function sendTripPlanMessage(
  payload: TripPlanMessageRequest,
): Promise<TripPlanMessagePostResponse> {
  const { data, error, response } = await apiClient.POST('/api/trip-plans/messages', {
    body: payload,
  })
  if (error || !data) throw buildApiError(response.status, error, '发送规划消息失败')
  return data
}

export async function listTripPlans(): Promise<TripPlanListResponse> {
  const { data, error, response } = await apiClient.GET('/api/trip-plans')
  if (error || !data) throw buildApiError(response.status, error, '获取历史对话失败')
  return data
}

export async function getTripPlanConversation(
  tripPlanId: string,
): Promise<TripPlanConversationResponse> {
  const { data, error, response } = await apiClient.GET('/api/trip-plans/{trip_plan_id}/messages', {
    params: {
      path: { trip_plan_id: tripPlanId },
    },
  })
  if (error || !data) throw buildApiError(response.status, error, '获取对话记录失败')
  return data
}

export async function getCandidateRouteDetail(
  tripPlanId: string,
  candidateId: string,
): Promise<CandidateRouteDetailResponse> {
  const { data, error, response } = await apiClient.GET(
    '/api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}',
    {
      params: {
        path: {
          trip_plan_id: tripPlanId,
          candidate_id: candidateId,
        },
      },
    },
  )
  if (error || !data) throw buildApiError(response.status, error, '获取候选线路详情失败')
  return data
}

export async function saveCandidateRoute(
  tripPlanId: string,
  candidateId: string,
): Promise<RoutePlanSnapshotDetailResponse> {
  const { data, error, response } = await apiClient.POST(
    '/api/trip-plans/{trip_plan_id}/candidate-routes/{candidate_id}/save',
    {
      params: {
        path: {
          trip_plan_id: tripPlanId,
          candidate_id: candidateId,
        },
      },
    },
  )
  if (error || !data) throw buildApiError(response.status, error, '保存规划失败')
  return data
}

export async function listRoutePlanSnapshots(): Promise<RoutePlanSnapshotListResponse> {
  const { data, error, response } = await apiClient.GET('/api/my/route-plan-snapshots')
  if (error || !data) throw buildApiError(response.status, error, '获取我的规划失败')
  return data
}

export async function getRoutePlanSnapshotDetail(
  snapshotId: string,
): Promise<RoutePlanSnapshotDetailResponse> {
  const { data, error, response } = await apiClient.GET(
    '/api/my/route-plan-snapshots/{snapshot_id}',
    {
      params: {
        path: { snapshot_id: snapshotId },
      },
    },
  )
  if (error || !data) throw buildApiError(response.status, error, '获取规划详情失败')
  return data
}

/** 带认证的 fetch 包装，用于非标准 API 请求（如文件下载） */
export async function apiFetch(url: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers || {})
  const token = localStorage.getItem('access_token')
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  return fetch(url, { ...options, headers })
}

/** 构造带 Bearer Token 的 Headers 对象 */
function authHeaders(): Headers {
  const headers = new Headers()
  const token = localStorage.getItem('access_token')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  return headers
}

/** 安全解析响应 JSON，空响应返回 null */
async function parseJson(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

/** 从后端错误响应中提取可读消息，失败时使用 fallback */
function buildApiError(status: number, payload: unknown, fallback: string) {
  return new ApiError(status, extractMessage(payload) || fallback, payload)
}

/** 从后端响应体中提取错误消息，兼容多种错误格式：
 * - { message: "..." } （业务错误）
 * - { detail: "..." } （FastAPI 验证错误字符串）
 * - { detail: [{ msg: "..." }] } （FastAPI 字段验证错误数组）
 */
function extractMessage(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object') return null
  const body = payload as Record<string, unknown>
  if (typeof body.message === 'string') return body.message
  if (typeof body.detail === 'string') return body.detail
  if (Array.isArray(body.detail)) {
    return body.detail
      .map((item) => {
        if (item && typeof item === 'object' && 'msg' in item) {
          return String((item as Record<string, unknown>).msg)
        }
        return String(item)
      })
      .join(', ')
  }
  return null
}
