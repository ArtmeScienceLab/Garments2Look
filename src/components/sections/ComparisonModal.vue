<script lang="ts" setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps<{
  visible: boolean
  methodName: string
  gtSrc: string
  methodSrc: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const splitPos = ref(50)       // 分割线位置 0~100%
const isDragging = ref(false)  // 是否正在拖拽
const isClickAnim = ref(false) // 是否正在执行点击动画
const containerRef = ref<HTMLElement | null>(null)

// 用于区分点击和拖拽：记录 mousedown 的起始位置
let startClientX = 0
let startClientY = 0
let hasMoved = false
const DRAG_THRESHOLD = 5 // 移动超过 5px 才算拖拽

let clickAnimTimer: number | undefined

/** 计算鼠标/触摸位置对应的百分比 */
const getPct = (clientX: number): number => {
  if (!containerRef.value) return splitPos.value
  const rect = containerRef.value.getBoundingClientRect()
  const x = clientX - rect.left
  return Math.min(100, Math.max(0, (x / rect.width) * 100))
}

/** 点击跳转，带非线性动画 */
const animateTo = (pct: number) => {
  if (clickAnimTimer !== undefined) window.clearTimeout(clickAnimTimer)
  isClickAnim.value = true
  splitPos.value = pct
  // 动画时长 450ms 后关闭动画标记
  clickAnimTimer = window.setTimeout(() => {
    isClickAnim.value = false
  }, 450)
}

// ── 鼠标事件 ──

const onBodyMouseDown = (e: MouseEvent) => {
  isDragging.value = true
  hasMoved = false
  startClientX = e.clientX
  startClientY = e.clientY
  e.preventDefault()
}

const onMouseMove = (e: MouseEvent) => {
  if (!isDragging.value) return
  const dx = Math.abs(e.clientX - startClientX)
  const dy = Math.abs(e.clientY - startClientY)
  if (dx > DRAG_THRESHOLD || dy > DRAG_THRESHOLD) {
    hasMoved = true
  }
  if (hasMoved) {
    // 拖拽：立即更新，无动画
    isClickAnim.value = false
    splitPos.value = getPct(e.clientX)
  }
}

const onMouseUp = (e: MouseEvent) => {
  if (!isDragging.value) return
  if (!hasMoved) {
    // 点击：带非线性动画跳到目标位置
    animateTo(getPct(e.clientX))
  }
  isDragging.value = false
  hasMoved = false
}

// ── 触摸事件 ──

const onTouchStart = (e: TouchEvent) => {
  isDragging.value = true
  hasMoved = false
  startClientX = e.touches[0].clientX
  startClientY = e.touches[0].clientY
  e.preventDefault()
}

const onTouchMove = (e: TouchEvent) => {
  if (!isDragging.value) return
  const dx = Math.abs(e.touches[0].clientX - startClientX)
  const dy = Math.abs(e.touches[0].clientY - startClientY)
  if (dx > DRAG_THRESHOLD || dy > DRAG_THRESHOLD) {
    hasMoved = true
  }
  if (hasMoved) {
    isClickAnim.value = false
    splitPos.value = getPct(e.touches[0].clientX)
  }
}

const onTouchEnd = (e: TouchEvent) => {
  if (!isDragging.value) return
  if (!hasMoved) {
    const touch = e.changedTouches[0]
    animateTo(getPct(touch.clientX))
  }
  isDragging.value = false
  hasMoved = false
}

const onOverlayClick = (e: MouseEvent) => {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    window.addEventListener('touchmove', onTouchMove, { passive: false })
    window.addEventListener('touchend', onTouchEnd)
  }
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
    window.removeEventListener('touchmove', onTouchMove)
    window.removeEventListener('touchend', onTouchEnd)
  }
  if (clickAnimTimer !== undefined) window.clearTimeout(clickAnimTimer)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="cm-overlay"
      @click="onOverlayClick"
    >
      <div class="cm-dialog">
        <div class="cm-header">
          <span class="cm-title">{{ methodName }}</span>
          <button class="cm-close-btn" type="button" @click="emit('close')">✕</button>
        </div>

        <div
          class="cm-body"
          ref="containerRef"
          :class="{ dragging: isDragging, animating: isClickAnim }"
          @mousedown="onBodyMouseDown"
          @touchstart.prevent="onTouchStart"
        >
          <!-- GT 图（底层，完整显示） -->
          <img class="cm-img cm-img-gt" :src="gtSrc" alt="GT" draggable="false" />

          <!-- 对比方法图（用 clip-path 裁剪，只显示右侧部分） -->
          <img
            class="cm-img cm-img-method"
            :src="methodSrc"
            :alt="methodName"
            draggable="false"
            :style="{ clipPath: `inset(0 0 0 ${splitPos}%)` }"
          />

          <!-- 分隔线（点击时跟随动画，拖拽时无动画） -->
          <div
            class="cm-divider"
            :style="{ left: splitPos + '%' }"
          >
            <div class="cm-divider-handle">
              <span class="cm-arrow cm-arrow-left">‹</span>
              <span class="cm-arrow cm-arrow-right">›</span>
            </div>
          </div>

          <!-- 左下角 GT 标签 -->
          <div class="cm-label cm-label-left">GT</div>
          <!-- 右下角方法名标签 -->
          <div class="cm-label cm-label-right">{{ methodName }}</div>
        </div>

        <div class="cm-hint">Click or drag to compare GT with method result</div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.cm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.78);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cm-dialog {
  background: #ffffff;
  border-radius: 10px;
  overflow: hidden;
  max-width: 90vw;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4);
}

.cm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #eeeeee;
  flex-shrink: 0;
}

.cm-title {
  font-size: 15px;
  font-weight: 600;
  color: #222222;
}

.cm-close-btn {
  border: none;
  background: transparent;
  font-size: 16px;
  cursor: pointer;
  color: #888888;
  padding: 0 4px;
  line-height: 1;
  transition: color 0.15s ease;
}

.cm-close-btn:hover {
  color: #222222;
}

.cm-body {
  position: relative;
  flex: 1;
  overflow: hidden;
  cursor: col-resize;
  min-height: 300px;
  max-height: calc(92vh - 100px);
  aspect-ratio: 3 / 4;
  width: min(70vh, 85vw);
  align-self: center;
}

.cm-body.dragging {
  cursor: col-resize;
}

/* 点击时：分隔线和裁剪路径一起用非线性动画移动到目标位置 */
.cm-body.animating .cm-divider {
  transition: left 0.45s cubic-bezier(0.34, 1.4, 0.64, 1);
}

.cm-body.animating .cm-img-method {
  transition: clip-path 0.45s cubic-bezier(0.34, 1.4, 0.64, 1);
}

.cm-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  user-select: none;
  -webkit-user-drag: none;
}

.cm-img-gt {
  z-index: 1;
}

.cm-img-method {
  z-index: 2;
}

.cm-divider {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #ffffff;
  z-index: 3;
  transform: translateX(-50%);
  cursor: col-resize;
  box-shadow: 0 0 6px rgba(0, 0, 0, 0.4);
}

.cm-divider-handle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1px;
  font-size: 14px;
  color: #555555;
  user-select: none;
}

.cm-label {
  position: absolute;
  bottom: 10px;
  padding: 3px 10px;
  background: rgba(0, 0, 0, 0.55);
  color: #ffffff;
  font-size: 12px;
  border-radius: 999px;
  pointer-events: none;
  z-index: 4;
}

.cm-label-left {
  left: 10px;
}

.cm-label-right {
  right: 10px;
}

.cm-hint {
  flex-shrink: 0;
  text-align: center;
  font-size: 12px;
  color: #888888;
  padding: 8px 16px;
  border-top: 1px solid #eeeeee;
}
</style>
