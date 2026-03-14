<script lang="ts" setup>
import { ref, watch, computed, onMounted, onBeforeUnmount } from 'vue'

type OutfitJson = {
  source: string
  gender: string
  outfit_info: {
    style?: string
    season?: string
    occasion?: string
    color_palette?: string[]
    theme?: string
    outfit_description?: string
    model_attributes?: {
      body?: string
      pose?: string
      background?: string
    }
    dressing_details?: {
      layering_structure?: { garment_id: string; layer: number }[]
      styling_techniques?: Record<string, string>
    }
  }
  outfit: Record<string, string>
}

const props = defineProps<{
  outfitId: string
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const loading = ref(false)
const error = ref<string | null>(null)
const detail = ref<OutfitJson | null>(null)
const activeTab = ref<'image' | 'basic'>('image')
// look 图可能是 .jpg 或 .png，先试 .jpg，失败则用 .png
const lookImageSrc = ref('')

const NARROW_BREAKPOINT = 768
const isNarrowScreen = ref(false)
const updateNarrow = () => {
  if (typeof window === 'undefined') return
  isNarrowScreen.value = window.innerWidth <= NARROW_BREAKPOINT
}
onMounted(() => {
  updateNarrow()
  window.addEventListener('resize', updateNarrow)
})
onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', updateNarrow)
  }
})

const handleClose = () => {
  emit('close')
}

const cache = new Map<string, OutfitJson>()

const loadDetail = async () => {
  if (!props.outfitId || !props.visible) return
  if (cache.has(props.outfitId)) {
    detail.value = cache.get(props.outfitId) || null
    error.value = null
    return
  }
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/dataset/${props.outfitId}/${props.outfitId}.json`)
    if (!res.ok) {
      throw new Error(`加载失败: ${res.status}`)
    }
    const data = (await res.json()) as OutfitJson
    detail.value = data
    cache.set(props.outfitId, data)
  } catch (e: any) {
    console.error(e)
    error.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function onLookImageError() {
  if (props.outfitId && lookImageSrc.value.endsWith('.jpg')) {
    lookImageSrc.value = `/dataset/${props.outfitId}/images/look/${props.outfitId}.png`
  }
}

// garment 图：dataset/{outfit_id}/images/garments/{garment_id}/{garment_id}.jpg，失败则试 .png，再失败用占位图
const garmentImageFallback = ref<Record<string, string>>({})
const GARMENT_PLACEHOLDER = '/dataset/loading.jpg'

function getGarmentImageSrc(garmentId: string): string {
  const key = `${props.outfitId}:${garmentId}`
  const fallback = garmentImageFallback.value[key]
  if (fallback) return fallback
  return `/dataset/${props.outfitId}/images/garments/${garmentId}/${garmentId}.jpg`
}

function onGarmentImageError(garmentId: string) {
  const key = `${props.outfitId}:${garmentId}`
  const existing = garmentImageFallback.value[key]
  if (!existing) {
    garmentImageFallback.value = {
      ...garmentImageFallback.value,
      [key]: `/dataset/${props.outfitId}/images/garments/${garmentId}/${garmentId}.png`,
    }
  } else if (existing.endsWith('.png')) {
    garmentImageFallback.value = { ...garmentImageFallback.value, [key]: GARMENT_PLACEHOLDER }
  }
}

function lockPageScroll() {
  if (typeof document === 'undefined') return
  document.documentElement.style.overflow = 'hidden'
  document.body.style.overflow = 'hidden'
}

function unlockPageScroll() {
  if (typeof document === 'undefined') return
  document.documentElement.style.overflow = ''
  document.body.style.overflow = ''
}

watch(
  () => props.outfitId,
  (id) => {
    if (id) {
      lookImageSrc.value = `/dataset/${id}/images/look/${id}.jpg`
      garmentImageFallback.value = {}
    }
  },
  { immediate: true }
)

watch(
  () => [props.outfitId, props.visible] as const,
  () => {
    if (props.visible) {
      activeTab.value = 'image'
      loadDetail()
      lockPageScroll()
    } else {
      unlockPageScroll()
    }
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  unlockPageScroll()
})

const garmentRows = computed(() => {
  if (!detail.value) return []
  const outfit = detail.value.outfit || {}
  const styling =
    detail.value.outfit_info?.dressing_details?.styling_techniques || {}
  const layeringRaw =
    detail.value.outfit_info?.dressing_details?.layering_structure || []

  // Layer 信息可能有两种格式：
  // 1) [{ garment_id: string, layer: number }, ...]
  // 2) ["P01050689", "P01079464", ...] 按顺序从 1 开始
  const layeringMap: Record<string, number> = {}
  layeringRaw.forEach((entry: any, idx: number) => {
    if (!entry) return
    if (typeof entry === 'string') {
      layeringMap[entry] = idx + 1
    } else if (typeof entry === 'object') {
      const id = entry.garment_id
      if (!id) return
      const layerVal =
        typeof entry.layer === 'number' && entry.layer > 0
          ? entry.layer
          : idx + 1
      layeringMap[id] = layerVal
    }
  })

  return Object.entries(outfit).map(([garmentId, name]) => {
    const layer = layeringMap[garmentId] ?? null
    const stylingText = styling[garmentId]
    const segmentImages: string[] = []
    // 先尝试 index 0～2，onerror 隐藏加载失败的图片
    for (let i = 0; i < 3; i++) {
      segmentImages.push(
        `/dataset/${props.outfitId}/images/segment/${garmentId}/${garmentId}-${i}.png`
      )
    }
    return {
      id: garmentId,
      name,
      styling: stylingText,
      layer,
      segmentImages,
    }
  })
})

const outfitInfo = computed(() => detail.value?.outfit_info || {})
const modelAttrs = computed(
  () => detail.value?.outfit_info?.model_attributes || {}
)
</script>

<template>
  <el-dialog
    :model-value="visible"
    width="70%"
    top="5vh"
    :fullscreen="isNarrowScreen"
    :close-on-click-modal="false"
    :lock-scroll="true"
    :append-to-body="true"
    :modal="true"
    @close="handleClose"
  >
    <template #header>
      <div class="modal-header">
        <span class="modal-title">Look Detail - {{ outfitId }}</span>
      </div>
    </template>

    <div class="modal-body">
      <div class="modal-left">
        <div class="look-image-wrapper">
          <img
            :src="lookImageSrc"
            alt="look"
            class="look-image"
            @error="onLookImageError"
          />
        </div>
      </div>
      <div class="modal-right">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="🧥 Garment Info" name="image">
            <div v-if="loading" class="state-text">Loading...</div>
            <div v-else-if="error" class="state-text error">{{ error }}</div>
            <div v-else-if="!detail" class="state-text">No data</div>
            <div v-else class="image-data-table">
              <div class="table-header-row">
                <div class="col-index">#</div>
                <div class="col-garment-img">Image</div>
                <div class="col-garment-info">Garment</div>
                <div class="col-garment-styling">Styling</div>
                <div class="col-garment-layer">Layer</div>
                <div class="col-garment-segment">Segments</div>
              </div>
              <div class="table-body">
                <div
                  v-for="(row, idx) in garmentRows"
                  :key="row.id"
                  class="table-row"
                >
                  <div class="col-index">
                    <span class="index-tag">{{ idx + 1 }}</span>
                  </div>
                  <div class="col-garment-img">
                    <div class="garment-thumb-placeholder">
                      <img
                        :src="getGarmentImageSrc(row.id)"
                        :alt="row.id"
                        @error="onGarmentImageError(row.id)"
                      />
                    </div>
                  </div>
                  <div class="col-garment-info">
                    <div class="garment-id">{{ row.id }}</div>
                    <div class="garment-name">{{ row.name }}</div>
                  </div>
                  <div class="col-garment-styling">
                    <template v-if="row.styling">
                      <span class="styling-tag">{{ row.styling }}</span>
                    </template>
                    <span v-else class="text-muted">No styling info</span>
                  </div>
                  <div class="col-garment-layer">
                    <span class="layer-tag">
                      {{ row.layer != null ? row.layer : '-' }}
                    </span>
                  </div>
                  <div class="col-garment-segment">
                    <div class="segment-images">
                      <img
                        v-for="img in row.segmentImages"
                        :key="img"
                        :src="img"
                        alt="segment"
                        class="segment-thumb"
                        loading="lazy"
                        @error="($event.target as HTMLImageElement).style.setProperty('display', 'none')"
                      />
                      <span
                        v-if="
                          !row.segmentImages ||
                          row.segmentImages.length === 0
                        "
                        class="text-muted small"
                      >
                        No segment images
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="ℹ️ Outfit Info" name="basic">
            <div v-if="loading" class="state-text">Loading...</div>
            <div v-else-if="error" class="state-text error">{{ error }}</div>
            <div v-else-if="!detail" class="state-text">No data</div>
            <div v-else class="basic-info">
              <div class="section">
                <div class="section-title">Outfit Info</div>
                <div class="info-grid">
                  <div class="info-item">
                    <span class="info-label">Style</span>
                    <span class="info-value">
                      {{ outfitInfo.style || '-' }}
                    </span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">Season</span>
                    <span class="info-value">
                      {{ outfitInfo.season || '-' }}
                    </span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">Occasion</span>
                    <span class="info-value">
                      {{ outfitInfo.occasion || '-' }}
                    </span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">Theme</span>
                    <span class="info-value">
                      {{ outfitInfo.theme || '-' }}
                    </span>
                  </div>
                  <div class="info-item info-item-full">
                    <span class="info-label">Description</span>
                    <span class="info-value multiline">
                      {{ outfitInfo.outfit_description || '-' }}
                    </span>
                  </div>
                  <div class="info-item info-item-full">
                    <span class="info-label">Colors</span>
                    <span class="info-value">
                      <template
                        v-if="
                          outfitInfo.color_palette &&
                          outfitInfo.color_palette.length
                        "
                      >
                        <span
                          v-for="c in outfitInfo.color_palette"
                          :key="c"
                          class="color-tag"
                        >
                          {{ c }}
                        </span>
                      </template>
                      <span v-else>-</span>
                    </span>
                  </div>
                </div>
              </div>

              <div class="section">
                <div class="section-title">Model Attributes</div>
                <div class="info-grid">
                  <div class="info-item info-item-full">
                    <span class="info-label">Body</span>
                    <span class="info-value multiline">
                      {{ modelAttrs.body || '-' }}
                    </span>
                  </div>
                  <div class="info-item info-item-full">
                    <span class="info-label">Pose</span>
                    <span class="info-value multiline">
                      {{ modelAttrs.pose || '-' }}
                    </span>
                  </div>
                  <div class="info-item info-item-full">
                    <span class="info-label">Background</span>
                    <span class="info-value multiline">
                      {{ modelAttrs.background || '-' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </el-dialog>
</template>

<style scoped>
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-title {
  font-weight: 600;
  font-size: 14px;
}

.modal-body {
  display: flex;
  gap: 16px;
  height: 70vh;
  max-height: 70vh;
  overflow: hidden;
}

.modal-left {
  flex: 0 0 40%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-right {
  flex: 0 0 60%;
  min-width: 0;
  padding-top: 8px;
  display: flex;
  flex-direction: column;
  /* 右侧允许上下滚动，禁止左右滚动 */
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.modal-right :deep(.el-tabs) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.modal-right :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
}

.modal-right :deep(.el-tab-pane) {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.modal-right :deep(.el-tab-pane > *) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.look-image-wrapper {
  width: 100%;
  height: 100%;
  min-height: 0;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.look-image {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
}

.state-text {
  padding: 16px 0;
  font-size: 13px;
  color: #666666;
}

.state-text.error {
  color: #d03050;
}

.image-data-table {
  margin-top: 4px;
  padding-top: 4px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.table-header-row,
.table-row {
  display: grid;
  grid-template-columns: 36px 70px 1.5fr 1fr 60px 1.5fr;
  column-gap: 8px;
  align-items: stretch;
}

.table-header-row {
  font-size: 12px;
  color: #888888;
  border-bottom: 1px solid #eeeeee;
  padding-bottom: 4px;
  margin-bottom: 4px;
}

.table-row {
  padding: 4px 0;
  border-bottom: 1px dashed #f0f0f0;
}

.table-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.col-index {
  display: flex;
  align-items: center;
  justify-content: center;
}

.index-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  border-radius: 999px;
  background: #f2f2f2;
  font-size: 11px;
}

.garment-thumb-placeholder {
  width: 100%;
  padding-top: 100%;
  position: relative;
  overflow: hidden;
  border-radius: 4px;
  background: #fafafa;
}

.garment-thumb-placeholder img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.col-garment-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
}

.garment-id {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
    'Liberation Mono', 'Courier New', monospace;
  font-size: 11px;
  color: #999999;
}

.garment-name {
  color: #333333;
}

.col-garment-styling {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  font-size: 12px;
}

.styling-tag {
  padding: 2px 6px;
  border-radius: 12px;
  background: #f5f0ff;
  color: #6b46c1;
  font-size: 11px;
}

.text-muted {
  color: #999999;
  font-size: 11px;
}

.text-muted.small {
  font-size: 10px;
}

.col-garment-layer {
  display: flex;
  align-items: center;
  justify-content: center;
}

.layer-tag {
  min-width: 24px;
  text-align: center;
  padding: 2px 4px;
  border-radius: 4px;
  background: #f5f5f5;
  font-size: 11px;
}

.col-garment-segment {
  display: flex;
  align-items: center;
}

.segment-images {
  display: flex;
  align-items: center;
  gap: 4px;
}

.segment-thumb {
  width: 32px;
  height: 48px;
  object-fit: cover;
  border-radius: 2px;
  border: 1px solid #f0f0f0;
}

.basic-info {
  margin-top: 4px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  overflow-y: auto;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 6px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 12px;
  row-gap: 8px;
  font-size: 12px;
}

.info-item {
  display: flex;
  gap: 4px;
}

.info-item-full {
  grid-column: 1 / -1;
}

.info-label {
  width: 52px;
  color: #666666;
  flex-shrink: 0;
}

.info-value {
  color: #333333;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.info-value.multiline {
  white-space: pre-wrap;
}

.color-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 6px;
  border-radius: 999px;
  font-size: 11px;
  background: #f5f5f5;
  margin-right: 4px;
  margin-bottom: 2px;
}

/* 小屏 / 竖屏：上下布局，图片固定比例与高度，表格可滚动 */
@media (max-width: 1024px) {
  .modal-body {
    flex-direction: column;
    height: auto;
    max-height: calc(100vh - 120px);
    /* 整个弹窗内容在小屏上统一上下滚动，禁止左右滚动 */
    overflow-y: auto;
    overflow-x: hidden;
  }

  .modal-left {
    flex: 0 0 auto;
    min-height: 0;
    max-height: 35vh;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .modal-left .look-image-wrapper {
    width: 100%;
    max-height: 35vh;
    aspect-ratio: 9 / 16;
    height: auto;
    flex-shrink: 0;
  }

  .modal-right {
    flex: 0 0 auto;
    min-height: 0;
    /* 小屏下由 .modal-body 负责滚动，这里不再单独滚动 */
    overflow: visible;
    display: flex;
    flex-direction: column;
  }

  .modal-right :deep(.el-tabs) {
    min-height: 0;
  }

  .modal-right :deep(.el-tabs__content) {
    flex: 1;
    min-height: 0;
  }

  .modal-right :deep(.el-tab-pane) {
    height: 100%;
    min-height: 0;
    display: flex;
    flex-direction: column;
  }

  .modal-right :deep(.el-tab-pane > *) {
    flex: 1;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .image-data-table {
    flex: 1;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .table-body {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }
}
</style>

