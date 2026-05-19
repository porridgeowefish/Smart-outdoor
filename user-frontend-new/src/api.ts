import createClient from 'openapi-fetch'
import type { components, paths } from './generated/openapi'

export type LoginRequest = components['schemas']['LoginRequest']
export type LoginResponse = components['schemas']['LoginResponse']
export type RegisterRequest = components['schemas']['RegisterRequest']
export type RegisterResponse = components['schemas']['RegisterResponse']
export type UserPublic = components['schemas']['UserPublic']
export type UserMe = components['schemas']['UserMe']
export type UserUpdateRequest = components['schemas']['UserUpdateRequest']
export type RouteListItem = components['schemas']['RouteListItem']
export type RouteListResponse = components['schemas']['RouteListResponse']
export type RouteUploadRequest = components['schemas']['RouteUploadRequest']
export type RouteUploadResponse = components['schemas']['RouteUploadResponse']
export type RouteDetailResponse = components['schemas']['RouteDetailResponse']
export type RouteFullTrackResponse = components['schemas']['RouteFullTrackResponse']
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
export type ImageAssetMetadata = components['schemas']['ImageAssetMetadata']
export type StorageObjectMetadata = components['schemas']['StorageObjectMetadata']
export type UploadCredentialResponse = components['schemas']['UploadCredentialResponse']

type UploadAssetType = 'avatar' | 'route_cover' | 'route_track_raw'
type UploadedObject = StorageObjectMetadata & {
  storage_provider: string
}

type PreparedImage = {
  blob: Blob
  width: number
  height: number
  contentType: string
}

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

export const apiClient = createClient<paths>({ baseUrl: '' })

apiClient.use({
  onRequest({ request }) {
    const token = localStorage.getItem('access_token')
    if (token && !request.headers.has('Authorization')) {
      request.headers.set('Authorization', `Bearer ${token}`)
    }
    return request
  },
})

export function hasAuthToken() {
  return Boolean(localStorage.getItem('access_token'))
}

export function clearAuthToken() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('token_type')
}

export async function login(payload: LoginRequest): Promise<LoginResponse> {
  const { data, error, response } = await apiClient.POST('/api/auth/login', {
    body: payload,
  })
  if (error || !data) throw buildApiError(response.status, error, 'Login failed')
  localStorage.setItem('access_token', data.access_token)
  localStorage.setItem('token_type', data.token_type)
  return data
}

export async function register(payload: RegisterRequest): Promise<RegisterResponse> {
  const { data, error, response } = await apiClient.POST('/api/auth/register', {
    body: payload,
  })
  if (error || !data) throw buildApiError(response.status, error, 'Register failed')
  return data
}

export async function getMe(): Promise<UserMe> {
  const { data, error, response } = await apiClient.GET('/api/me')
  if (error || !data) throw buildApiError(response.status, error, 'Failed to load user')
  return data
}

export async function updateMe(payload: UserUpdateRequest): Promise<UserMe> {
  const { data, error, response } = await apiClient.PATCH('/api/me', {
    body: payload,
  })
  if (error || !data) throw buildApiError(response.status, error, 'Failed to update user')
  return data
}

export async function uploadAvatar(file: File): Promise<UserMe> {
  const [display, thumbnail] = await Promise.all([
    prepareImage(file, 512, 0.86),
    prepareImage(file, 128, 0.82),
  ])
  const [displayObject, thumbnailObject] = await Promise.all([
    uploadObject({
      assetType: 'avatar',
      blob: display.blob,
      originalFilename: file.name,
      contentType: display.contentType,
      variant: 'display',
      width: display.width,
      height: display.height,
    }),
    uploadObject({
      assetType: 'avatar',
      blob: thumbnail.blob,
      originalFilename: file.name,
      contentType: thumbnail.contentType,
      variant: 'thumbnail',
      width: thumbnail.width,
      height: thumbnail.height,
    }),
  ])
  return updateMe({
    avatar: buildImageAsset(file.name, displayObject, {
      display: displayObject,
      thumbnail: thumbnailObject,
    }),
  })
}

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
  if (error || !data) throw buildApiError(response.status, error, 'Failed to load routes')
  return data
}

export async function getRouteDetail(routeId: string): Promise<RouteDetailResponse> {
  const { data, error, response } = await apiClient.GET('/api/routes/{route_id}', {
    params: {
      path: { route_id: routeId },
    },
  })
  if (error || !data) throw buildApiError(response.status, error, 'Failed to load route detail')
  return data
}

export async function getRouteTrack(routeId: string): Promise<RouteFullTrackResponse> {
  const { data, error, response } = await apiClient.GET('/api/routes/{route_id}/track', {
    params: {
      path: { route_id: routeId },
    },
  })
  if (error || !data) throw buildApiError(response.status, error, 'Failed to load route track')
  return data
}

export async function getRouteTagTaxonomy(): Promise<RouteTagTaxonomyResponse> {
  const { data, error } = await apiClient.GET('/api/routes/tag-taxonomy')
  if (error || !data) throw buildApiError(500, error, 'Failed to load route tags')
  return data
}

export async function uploadRoute(payload: {
  file: File
  coverImage?: File | null
  name: string
  description?: string
  visibility: 'public' | 'private'
  manualTags?: Record<string, unknown>
}): Promise<RouteUploadResponse> {
  const trackObjectPromise = uploadObject({
    assetType: 'route_track_raw',
    blob: payload.file,
    originalFilename: payload.file.name,
    contentType: routeTrackContentType(payload.file),
    variant: 'raw',
  })
  const coverImagePromise = payload.coverImage ? uploadRouteCover(payload.coverImage) : Promise.resolve(null)

  const [trackObject, coverImage] = await Promise.all([trackObjectPromise, coverImagePromise])
  const body: RouteUploadRequest = {
    name: payload.name,
    description: payload.description?.trim() || null,
    visibility: payload.visibility,
    manual_tags: payload.manualTags ?? null,
    track_file: {
      storage_provider: trackObject.storage_provider,
      storage_key: trackObject.storage_key,
      file_url: trackObject.url,
      file_type: routeTrackFileType(payload.file),
      content_type: trackObject.content_type,
      size_bytes: trackObject.size_bytes,
      original_filename: payload.file.name,
    },
    cover_image: coverImage,
  }

  const { data, error, response } = await apiClient.POST('/api/routes/upload', { body })
  if (error || !data) throw buildApiError(response.status, error, 'Failed to upload route')
  return data
}

export async function getAbilityProfile(): Promise<AbilityProfileResponse | null> {
  const { data, error, response } = await apiClient.GET('/api/me/ability-profile')
  if (response.status === 404) return null
  if (error || !data) throw buildApiError(response.status, error, 'Failed to load ability profile')
  return data
}

export async function listActivityTracks(): Promise<ActivityTrackListResponse> {
  const { data, error, response } = await apiClient.GET('/api/me/activity-tracks')
  if (error || !data) throw buildApiError(response.status, error, 'Failed to load activity tracks')
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
  if (!response.ok) throw buildApiError(response.status, body, 'Failed to upload activity track')
  return body as ActivityUploadResponse
}

export async function sendTripPlanMessage(
  payload: TripPlanMessageRequest,
): Promise<TripPlanMessagePostResponse> {
  const { data, error, response } = await apiClient.POST('/api/trip-plans/messages', {
    body: payload,
  })
  if (error || !data) throw buildApiError(response.status, error, 'Failed to send trip plan message')
  return data
}

export async function listTripPlans(): Promise<TripPlanListResponse> {
  const { data, error, response } = await apiClient.GET('/api/trip-plans')
  if (error || !data) throw buildApiError(response.status, error, 'Failed to load trip plans')
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
  if (error || !data) throw buildApiError(response.status, error, 'Failed to load conversation')
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
  if (error || !data) throw buildApiError(response.status, error, 'Failed to load candidate route')
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
  if (error || !data) throw buildApiError(response.status, error, 'Failed to save route plan')
  return data
}

export async function listRoutePlanSnapshots(): Promise<RoutePlanSnapshotListResponse> {
  const { data, error, response } = await apiClient.GET('/api/my/route-plan-snapshots')
  if (error || !data) throw buildApiError(response.status, error, 'Failed to load saved plans')
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
  if (error || !data) throw buildApiError(response.status, error, 'Failed to load saved plan')
  return data
}

export async function apiFetch(url: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers || {})
  const token = localStorage.getItem('access_token')
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  return fetch(url, { ...options, headers })
}

async function uploadRouteCover(file: File): Promise<ImageAssetMetadata> {
  const [large, thumbnail] = await Promise.all([
    prepareImage(file, 1280, 0.84),
    prepareImage(file, 480, 0.82),
  ])
  const [largeObject, thumbnailObject] = await Promise.all([
    uploadObject({
      assetType: 'route_cover',
      blob: large.blob,
      originalFilename: file.name,
      contentType: large.contentType,
      variant: 'large',
      width: large.width,
      height: large.height,
    }),
    uploadObject({
      assetType: 'route_cover',
      blob: thumbnail.blob,
      originalFilename: file.name,
      contentType: thumbnail.contentType,
      variant: 'thumbnail',
      width: thumbnail.width,
      height: thumbnail.height,
    }),
  ])
  return buildImageAsset(file.name, largeObject, {
    large: largeObject,
    thumbnail: thumbnailObject,
  })
}

function buildImageAsset(
  originalFilename: string,
  primary: UploadedObject,
  variants: Record<string, UploadedObject>,
): ImageAssetMetadata {
  const cleanedVariants: Record<string, StorageObjectMetadata> = {}
  Object.entries(variants).forEach(([name, object]) => {
    cleanedVariants[name] = storageObjectMetadata(object)
  })

  return {
    storage_provider: primary.storage_provider,
    storage_key: primary.storage_key,
    url: primary.url,
    original_filename: originalFilename,
    processing_status: 'ready',
    variants: cleanedVariants,
  }
}

function storageObjectMetadata(object: UploadedObject): StorageObjectMetadata {
  return {
    storage_key: object.storage_key,
    url: object.url,
    width: object.width ?? null,
    height: object.height ?? null,
    content_type: object.content_type,
    size_bytes: object.size_bytes,
  }
}

async function uploadObject(payload: {
  assetType: UploadAssetType
  blob: Blob
  originalFilename: string
  contentType: string
  variant?: string
  width?: number
  height?: number
}): Promise<UploadedObject> {
  const { data, error, response } = await apiClient.POST('/api/storage/upload-credentials', {
    body: {
      asset_type: payload.assetType,
      variant: payload.variant ?? null,
      content_type: payload.contentType,
      original_filename: payload.originalFilename,
      size_bytes: payload.blob.size,
    },
  })
  if (error || !data) throw buildApiError(response.status, error, 'Failed to create upload credential')

  const headers = new Headers(data.headers)
  const isLocalUpload = data.upload_url.startsWith('/api/')
  if (isLocalUpload) {
    const token = localStorage.getItem('access_token')
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }

  const uploadResponse = await fetch(data.upload_url, {
    method: 'PUT',
    headers,
    body: payload.blob,
  })
  const uploadBody = await parseJson(uploadResponse)
  if (!uploadResponse.ok) {
    throw buildApiError(uploadResponse.status, uploadBody, 'Failed to upload object')
  }

  return {
    storage_provider: data.storage_provider,
    storage_key: data.storage_key,
    url: data.public_url,
    width: payload.width ?? null,
    height: payload.height ?? null,
    content_type: payload.contentType,
    size_bytes: payload.blob.size,
  }
}

async function prepareImage(file: File, maxEdge: number, quality: number): Promise<PreparedImage> {
  const image = await loadImage(file)
  const scale = Math.min(1, maxEdge / Math.max(image.naturalWidth, image.naturalHeight))
  const width = Math.max(1, Math.round(image.naturalWidth * scale))
  const height = Math.max(1, Math.round(image.naturalHeight * scale))
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('Canvas is unavailable')
  ctx.drawImage(image, 0, 0, width, height)

  const contentType = 'image/webp'
  const blob = await canvasToBlob(canvas, contentType, quality)
  return { blob, width, height, contentType }
}

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    const url = URL.createObjectURL(file)
    image.onload = () => {
      URL.revokeObjectURL(url)
      resolve(image)
    }
    image.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Failed to decode image'))
    }
    image.src = url
  })
}

function canvasToBlob(canvas: HTMLCanvasElement, type: string, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        reject(new Error('Failed to encode image'))
        return
      }
      resolve(blob)
    }, type, quality)
  })
}

function routeTrackFileType(file: File) {
  const lower = file.name.toLowerCase()
  if (lower.endsWith('.gpx')) return 'gpx'
  if (lower.endsWith('.kml')) return 'kml'
  if (lower.endsWith('.geojson') || lower.endsWith('.json')) return 'geojson'
  return 'unknown'
}

function routeTrackContentType(file: File) {
  const lower = file.name.toLowerCase()
  if (lower.endsWith('.gpx')) return 'application/gpx+xml'
  if (lower.endsWith('.kml')) return 'application/vnd.google-earth.kml+xml'
  if (lower.endsWith('.geojson') || lower.endsWith('.json')) return 'application/geo+json'
  return file.type || 'application/octet-stream'
}

function authHeaders(): Headers {
  const headers = new Headers()
  const token = localStorage.getItem('access_token')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  return headers
}

async function parseJson(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function buildApiError(status: number, payload: unknown, fallback: string) {
  return new ApiError(status, extractMessage(payload) || fallback, payload)
}

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
