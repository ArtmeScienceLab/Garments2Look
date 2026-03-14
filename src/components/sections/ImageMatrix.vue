<script lang="ts" setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import OutfitDetailModal from './OutfitDetailModal.vue'

// 展示顺序由父组件传入，例如：['P01006072_b1', 'P00787009_b1', ...]
const props = defineProps<{
  orderList: string[]
}>()

// 本地 dev 时 public 在根路径；部署到 GitHub Pages 时用 BASE_URL（/Garments2Look/），保证末尾有斜杠
const _base = import.meta.env.DEV ? '/' : (import.meta.env.BASE_URL || '/')
const baseUrl = _base.endsWith('/') ? _base : _base + '/'

// 缩略图约定（优先加载省流，缺失则自动回退原图）：look/thumb/{id}.jpg、segment/thumb/color_segmentation.png、dwpose/thumb/{id}.png

// 最小和最大列数
const MIN_COLS = 4
const MAX_COLS = 8

const cols = ref<number>(MIN_COLS)

const calcCols = () => {
  if (typeof window === 'undefined') return
  const width = window.innerWidth
  let c = MIN_COLS

  if (width < 768) {
    c = 4
  } else if (width < 1200) {
    c = 6
  } else if (width < 1600) {
    c = 8
  } else {
    c = 8
  }

  cols.value = Math.min(MAX_COLS, Math.max(MIN_COLS, c))
}

// 自动轮播相关
const AUTO_PLAY_INTERVAL = 10000
let autoPlayTimer: number | undefined
// 用于驱动自动翻页进度条动画重启
const progressSeed = ref(0)

const resetAutoPlay = () => {
  if (typeof window === 'undefined') return
  if (autoPlayTimer !== undefined) {
    window.clearInterval(autoPlayTimer)
  }
  autoPlayTimer = window.setInterval(() => {
    goToNextPage()
  }, AUTO_PLAY_INTERVAL)
  // 重启进度条动画
  progressSeed.value++
}

onMounted(() => {
  calcCols()
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', calcCols)
  }
  resetAutoPlay()
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', calcCols)
    if (autoPlayTimer !== undefined) {
      window.clearInterval(autoPlayTimer)
    }
  }
})

// 计算两行展示所需的格子数量
const cells = computed(() => cols.value * 2)

// 固定总页数为 4 页
const TOTAL_PAGES = 2
const currentPage = ref(0)
// 记录最近一次翻页方向：1 表示向右（下一页），-1 表示向左（上一页）
const lastDirection = ref<1 | -1>(1)

const startPageTransition = (updatePage: () => void) => {
  // 正在做波浪翻页动画时，忽略新的翻页请求，避免动画被打断
  if (isTransitioning.value) return

  // 记录当前页内容作为上一页，用于做淡出动画
  prevItems.value = displayItems.value
  isTransitioning.value = true
  animationSeed.value++

  updatePage()
  resetAutoPlay()

  if (typeof window !== 'undefined') {
    const maxDelay = (cols.value - 1) * 80 // 每列的延时
    const duration = 400 // 动画时长 ms
    window.setTimeout(() => {
      prevItems.value = null
      isTransitioning.value = false
    }, maxDelay + duration + 80)
  }
}

const goToPrevPage = () => {
  lastDirection.value = -1
  startPageTransition(() => {
    currentPage.value = (currentPage.value - 1 + TOTAL_PAGES) % TOTAL_PAGES
  })
}

const goToNextPage = () => {
  lastDirection.value = 1
  startPageTransition(() => {
    currentPage.value = (currentPage.value + 1) % TOTAL_PAGES
  })
}

type DisplayItem = {
  id: string
  mainSrc: string
  mainThumbSrc: string
  overlaySrc: string
  overlayThumbSrc: string
  skeletonSrc: string
  skeletonThumbSrc: string
}

// 用于触发每次翻页时的动画（变化时强制重算）
const animationSeed = ref(0)

// 上一页数据，用于做翻页时的交叉渐变
const prevItems = ref<DisplayItem[] | null>(null)
const isTransitioning = ref(false)

// 使用 loading 占位图补齐两行，每页固定显示同样数量的格子
const displayItems = computed<DisplayItem[]>(() => {
  const ids = props.orderList || []
  const totalPerPage = cells.value

  if (totalPerPage <= 0) return []

  const items: DisplayItem[] = []

  for (let i = 0; i < totalPerPage; i++) {
    // 每页用 totalPerPage 个格子（两行×列数），按页取 orderList 的连续一段
    const globalIndex = currentPage.value * totalPerPage + i
    if (globalIndex < ids.length) {
      const id = ids[globalIndex]
      if (id) {
        const mainSrc = `${baseUrl}dataset/${id}/images/look/${id}.jpg`
        const overlaySrc = `${baseUrl}dataset/${id}/images/segment/color_segmentation.png`
        const skeletonSrc = `${baseUrl}dataset/${id}/images/dwpose/${id}.png`

        items.push({
          id,
          mainSrc,
          mainThumbSrc: mainSrc.replace(`${baseUrl}dataset/`, `${baseUrl}thumbnail/`),
          overlaySrc,
          overlayThumbSrc: overlaySrc.replace(`${baseUrl}dataset/`, `${baseUrl}thumbnail/`),
          skeletonSrc,
          skeletonThumbSrc: skeletonSrc.replace(`${baseUrl}dataset/`, `${baseUrl}thumbnail/`),
        })
        continue
      }
    }

    // 没有显式指定 id 的格子统一使用 loading 占位图
    items.push({
      id: `placeholder-${currentPage.value}-${i}`,
      mainSrc: `${baseUrl}dataset/loading.jpg`,
      mainThumbSrc: `${baseUrl}dataset/loading.jpg`,
      overlaySrc: `${baseUrl}dataset/loading.jpg`,
      overlayThumbSrc: `${baseUrl}dataset/loading.jpg`,
      skeletonSrc: `${baseUrl}dataset/loading.jpg`,
      skeletonThumbSrc: `${baseUrl}dataset/loading.jpg`,
    })
  }

  return items
})

// 矩阵图优先用缩略图（省流），404 再回退原图；look 还有 jpg→png 回退
const lookUrlCache = ref<Record<string, string>>({})
const overlayUrlCache = ref<Record<string, string>>({})
const skeletonUrlCache = ref<Record<string, string>>({})

function getMainLookSrc(item: DisplayItem): string {
  return lookUrlCache.value[item.id] ?? item.mainThumbSrc ?? item.mainSrc
}

function onLookImageError(item: DisplayItem) {
  if (item.id.startsWith('placeholder-')) return
  const tried = lookUrlCache.value[item.id] ?? item.mainThumbSrc ?? item.mainSrc
  if (tried === item.mainThumbSrc) {
    lookUrlCache.value = { ...lookUrlCache.value, [item.id]: item.mainSrc }
  } else if (tried.endsWith('.jpg')) {
    lookUrlCache.value = {
      ...lookUrlCache.value,
      [item.id]: `${baseUrl}dataset/${item.id}/images/look/${item.id}.png`,
    }
  }
}

function getOverlaySrc(item: DisplayItem): string {
  return overlayUrlCache.value[item.id] ?? item.overlayThumbSrc ?? item.overlaySrc
}

function onOverlayError(item: DisplayItem) {
  if (item.id.startsWith('placeholder-')) return
  const tried = overlayUrlCache.value[item.id] ?? item.overlayThumbSrc ?? item.overlaySrc
  if (tried === item.overlayThumbSrc) {
    overlayUrlCache.value = { ...overlayUrlCache.value, [item.id]: item.overlaySrc }
  }
}

function getSkeletonSrc(item: DisplayItem): string {
  return skeletonUrlCache.value[item.id] ?? item.skeletonThumbSrc ?? item.skeletonSrc
}

function onSkeletonError(item: DisplayItem) {
  if (item.id.startsWith('placeholder-')) return
  const tried = skeletonUrlCache.value[item.id] ?? item.skeletonThumbSrc ?? item.skeletonSrc
  if (tried === item.skeletonThumbSrc) {
    skeletonUrlCache.value = { ...skeletonUrlCache.value, [item.id]: item.skeletonSrc }
  }
}

const activeOutfitId = ref<string | null>(null)
const isDetailVisible = ref(false)

const openDetail = (id: string) => {
  // 占位图不打开详情
  if (!id || id.startsWith('placeholder-')) return
  activeOutfitId.value = id
  isDetailVisible.value = true
  // 打开详情时暂停自动轮播
  if (typeof window !== 'undefined' && autoPlayTimer !== undefined) {
    window.clearInterval(autoPlayTimer)
    autoPlayTimer = undefined
  }
}

const closeDetail = () => {
  isDetailVisible.value = false
  activeOutfitId.value = null
  resetAutoPlay()
}
</script>

<template>
  <div class="image-matrix-wrapper">
    <el-row justify="center">
      <el-col :xs="24" :sm="22" :md="20" :lg="18" :xl="16">
        <div class="image-matrix-shell">
          <!-- 当前页 -->
          <div
            class="image-matrix-grid"
            :style="{ gridTemplateColumns: `repeat(${cols}, 1fr)` }"
          >
            <div
              v-for="(item, idx) in displayItems"
              :key="`current-${animationSeed}-${idx}`"
              class="image-cell"
            >
              <div class="image-inner">
                <img
                  class="image-base"
                  :src="getMainLookSrc(item)"
                  alt=""
                  loading="lazy"
                  @error="onLookImageError(item)"
                />
                <img
                  class="image-overlay"
                  :src="getOverlaySrc(item)"
                  alt=""
                  loading="lazy"
                  @error="onOverlayError(item)"
                />
                <img
                  class="image-skeleton"
                  :src="getSkeletonSrc(item)"
                  alt=""
                  loading="lazy"
                  @error="onSkeletonError(item)"
                />
                <button
                  class="image-detail-trigger"
                  type="button"
                  @click.stop="openDetail(item.id)"
                >
                  🔎Detail
                </button>
              </div>
            </div>
          </div>

          <!-- 上一页：做从左到右的淡出动画，盖在当前页上方 -->
          <div
            v-if="prevItems && isTransitioning"
            class="image-matrix-layer-prev"
          >
            <div
              class="image-matrix-grid"
              :style="{ gridTemplateColumns: `repeat(${cols}, 1fr)` }"
            >
              <div
                v-for="(item, idx) in prevItems"
                :key="`prev-${animationSeed}-${idx}`"
                class="image-cell page-fade-out"
                :style="{
                  animationDelay: `${
                    // 根据翻页方向控制波浪方向：
                    // 向右翻页：从左到右；向左翻页：从右到左
                    (lastDirection === 1
                      ? idx % cols
                      : cols - 1 - (idx % cols)) * 80
                  }ms`,
                }"
              >
                <div class="image-inner">
                  <img
                    class="image-base"
                    :src="getMainLookSrc(item)"
                    alt=""
                    loading="lazy"
                    @error="onLookImageError(item)"
                  />
                  <img
                    class="image-overlay"
                    :src="getOverlaySrc(item)"
                    alt=""
                    loading="lazy"
                    @error="onOverlayError(item)"
                  />
                  <img
                    class="image-skeleton"
                    :src="getSkeletonSrc(item)"
                    alt=""
                    loading="lazy"
                    @error="onSkeletonError(item)"
                  />
                </div>
              </div>
            </div>
          </div>

          <div class="page-progress-bar">
            <div
              class="page-progress-bar-inner"
              :key="progressSeed"
              :style="{
                animationDuration: AUTO_PLAY_INTERVAL + 'ms',
                animationPlayState: isDetailVisible ? 'paused' : 'running',
              }"
            ></div>
          </div>

          <div class="image-matrix-controls">
            <button
              class="nav-btn"
              type="button"
              :disabled="isTransitioning"
              @click="goToPrevPage"
            >
              ‹
            </button>
            <span class="page-indicator">
              Page {{ currentPage + 1 }} / {{ TOTAL_PAGES }}
            </span>
            <button
              class="nav-btn"
              type="button"
              :disabled="isTransitioning"
              @click="goToNextPage"
            >
              ›
            </button>
          </div>

          <OutfitDetailModal
            v-if="activeOutfitId"
            :visible="isDetailVisible"
            :outfit-id="activeOutfitId"
            @close="closeDetail"
          />
        </div>
        <div class="image-matrix-caption">
          👗 Default: try-on image · 🧩 Hover: segmentation · 🦴 Press: skeleton
          &nbsp;&nbsp;·&nbsp;&nbsp;
          <span class="caption-detail-hint">
            Click 🔎Detail to view Garment Info and Outfit Info.
          </span>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.image-matrix-wrapper {
  margin-top: 10px;
  margin-bottom: 10px;
}

.image-matrix-shell {
  position: relative;
}

.page-progress-bar {
  position: relative;
  margin-top: 6px;
  height: 3px;
  background: #f2f2f2;
  border-radius: 999px;
  overflow: hidden;
}

.page-progress-bar-inner {
  height: 100%;
  width: 0;
  background: #409eff;
  animation-name: page-progress-fill;
  animation-timing-function: linear;
  animation-fill-mode: forwards;
}

@keyframes page-progress-fill {
  from {
    width: 0%;
  }
  to {
    width: 100%;
  }
}

.image-matrix-grid {
  display: grid;
  gap: 0;
}
.image-cell {
  position: relative;
  width: 100%;
  /* 固定高宽比：高约 16，宽约 9（纵向） */
  padding-top: 177.7778%;
  overflow: hidden;
}

.image-matrix-layer-prev {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.page-fade-out {
  animation: image-matrix-fade-out 0.4s ease-out forwards;
}

@keyframes image-matrix-fade-out {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}

.image-inner {
  position: absolute;
  inset: 0;
}

.image-inner img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.image-base {
  position: absolute;
  inset: 0;
}

.image-overlay {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.3s ease-in-out;
}

.image-cell:hover .image-overlay {
  opacity: 1;
}

.image-skeleton {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.15s ease-in-out;
}

/* 鼠标按下时叠加展示 skeleton，分割图保持可见以避免闪回原图 */
.image-cell:active .image-skeleton {
  opacity: 1;
}

.image-matrix-caption {
  margin-top: 6px;
  font-size: 12px;
  color: #666666;
  text-align: center;
}
.caption-detail-hint {
  font-size: 12px;
  color: #666666;
}

.image-matrix-controls {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 12px;
  color: #666666;
}

.nav-btn {
  border: none;
  border-radius: 999px;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f2f2f2;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.1s ease;
}

.nav-btn[disabled] {
  opacity: 0.5;
  cursor: default;
  background: #f0f0f0;
}

.nav-btn[disabled]:hover,
.nav-btn[disabled]:active {
  background: #f0f0f0;
  transform: none;
}

.nav-btn:hover {
  background: #e0e0e0;
}

.nav-btn:active {
  transform: scale(0.95);
}

.page-indicator {
  min-width: 90px;
  text-align: center;
}

.image-detail-trigger {
  position: absolute;
  right: 6px;
  bottom: 6px;
  padding: 2px 8px;
  font-size: 11px;
  border-radius: 999px;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  color: #ffffff;
  cursor: pointer;
  opacity: 0;
  transform: translateY(4px);
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.image-cell:hover .image-detail-trigger {
  opacity: 1;
  transform: translateY(0);
}

.image-detail-trigger:hover {
  background: rgba(0, 0, 0, 0.8);
}
</style>

