<script lang="ts" setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import ComparisonModal from './ComparisonModal.vue'

// ─────────────────────────────────────────────
// 用户可修改的数据配置区域
// ─────────────────────────────────────────────

/** 每页展示一个 ID，garmentCount 表示 garment_1~N 的数量 */
const comparisonIds = [
  { 
    id: '164574102',
    garmentCount: 4
  },{
    id: 'P00787009_b1',
    garmentCount: 5
  },{
    id: 'P00913633_b1',
    garmentCount: 5
  },{
    id: '31528215',
    garmentCount: 6
  },{
    id: 'P00572751_b1',
    garmentCount: 6
  },{
    id: 'P00776037-P00858837-P00998826-P01054996-P01066514-P01068797',
    garmentCount: 6
  },{
    id: 'P00877882-P01057459-P01062109-P01075888-P01137029-P01138540',
    garmentCount: 6
  },{
    id: 'P01072121-P01073919-P01077248-P01080148-P01081747-P01086373',
    garmentCount: 6 
  },{
    id: '8933008',
    garmentCount: 7
  },{
    id: 'P00569534-P00965108-P01011271-P01047729-P01067146-P01078450-P01125007',
    garmentCount: 7
  },{
    id: 'P00932855-P00992488-P01025428-P01030171-P01048815-P01055564-P01129758',
    garmentCount: 7 
  },
]

type MethodMeta = { displayName: string; modelName: string; strategy: string }

/**
 * 方法字典：文件名 stem（不含 .png）→ { displayName, strategy }
 * strategy 可选值：'虚拟试穿方法' | '编辑（2 Ref）' | '编辑（N Ref）'
 */
const methodDict: Record<string, MethodMeta> = {
  'bootcomp-Inpainting':                                { displayName: 'BootComp',                         modelName: 'BootComp',              strategy: 'VTON' },
  'fastfit-Inpainting':                                 { displayName: 'FastFit',                          modelName: 'FastFit',               strategy: 'VTON' },
  'ip-adapter-inpainting':                              { displayName: 'IP-Adapter',                       modelName: 'IP-Adapter',            strategy: 'VTON' },
  'omnitry-Inpainting':                                 { displayName: 'OmniTry',                          modelName: 'OmniTry',               strategy: 'VTON' },

  'gpt-1-inpainting-model+ootd':                        { displayName: 'GPT-Image-1 + OOTD',               modelName: 'GPT-Image-1',           strategy: 'Edit (2 Ref)' },
  'gpt-1-5-inpainting-model+ootd':                      { displayName: 'GPT-Image-1.5 + OOTD',             modelName: 'GPT-Image-1.5',         strategy: 'Edit (2 Ref)' },
  'banana-1-inpainting-model+ootd':                     { displayName: 'Banana 1 + OOTD',                  modelName: 'Banana 1',              strategy: 'Edit (2 Ref)' },
  'banana-2-inpainting-model+ootd':                     { displayName: 'Banana Pro + OOTD',                modelName: 'Banana Pro',            strategy: 'Edit (2 Ref)' },
  'seedream-4-0-inpainting-model+ootd':                 { displayName: 'Seedream 4.0 + OOTD',              modelName: 'Seedream 4.0',          strategy: 'Edit (2 Ref)' },
  'seedream-4-5-inpainting-model+ootd-50%-Resized':     { displayName: 'Seedream 4.5 + OOTD',              modelName: 'Seedream 4.5',          strategy: 'Edit (2 Ref)' },
  'flux-2-inpainting-model+ootd':                       { displayName: 'FLUX-2 + OOTD',                    modelName: 'FLUX-2',                strategy: 'Edit (2 Ref)' },
  '2509-inpainting-model+ootd':                         { displayName: 'Qwen-Image-Edit-2509 + OOTD',      modelName: 'Qwen-Image-Edit-2509',  strategy: 'Edit (2 Ref)' },
  '2511-inpainting-model+ootd':                         { displayName: 'Qwen-Image-Edit-2511 + OOTD',      modelName: 'Qwen-Image-Edit-2511',  strategy: 'Edit (2 Ref)' },

  '2509-2-refer-10000samples-lora-inpainting':          { displayName: 'Ours (LoRA, 2 Ref)',               modelName: 'Ours (LoRA, 2 Ref)',    strategy: 'Edit (2 Ref)' },

  'gpt-1-inpainting-model+garments':                    { displayName: 'GPT-Image-1 + N',                  modelName: 'GPT-Image-1',           strategy: 'Edit (N Ref)' },
  'gpt-1-5-inpainting-model+garments':                  { displayName: 'GPT-Image-1.5 + N',                modelName: 'GPT-Image-1.5',         strategy: 'Edit (N Ref)' },
  'banana-1-inpainting-model+garments':                 { displayName: 'Banana 1 + N',                     modelName: 'Banana 1',              strategy: 'Edit (N Ref)' },
  'banana-2-inpainting-model+garments':                 { displayName: 'Banana Pro + N',                   modelName: 'Banana Pro',            strategy: 'Edit (N Ref)' },
  'seedream-4-0-inpainting-model+garments':             { displayName: 'Seedream 4.0 + N',                 modelName: 'Seedream 4.0',          strategy: 'Edit (N Ref)' },
  'seedream-4-5-inpainting-model+garments-50%-Resized': { displayName: 'Seedream 4.5 + N',                 modelName: 'Seedream 4.5',          strategy: 'Edit (N Ref)' },
  'flux-2-inpainting-model+garments':                   { displayName: 'FLUX-2 + N',                       modelName: 'FLUX-2',                strategy: 'Edit (N Ref)' },
  '2509-inpainting-model+garments':                     { displayName: 'Qwen Image Edit 2509 + N',         modelName: 'Qwen-Image-Edit-2509',  strategy: 'Edit (N Ref)' },
  '2511-inpainting-model+garments':                     { displayName: 'Qwen Image Edit 2511 + N',         modelName: 'Qwen-Image-Edit-2511',  strategy: 'Edit (N Ref)' },
}

// ─────────────────────────────────────────────
// Base URL（兼容 dev / GitHub Pages 部署）
// ─────────────────────────────────────────────
const _base = import.meta.env.DEV ? '/' : (import.meta.env.BASE_URL || '/')
const baseUrl = _base.endsWith('/') ? _base : _base + '/'

// ─────────────────────────────────────────────
// 筛选状态
// ─────────────────────────────────────────────
const ALL_STRATEGIES = ['VTON', 'Edit (2 Ref)', 'Edit (N Ref)']

/** 所有方法 stem 列表（按 methodDict 顺序） */
const allMethodStems = Object.keys(methodDict)

/** 已选的参考图策略（默认只选 VTON 和 Edit (2 Ref)） */
const selectedStrategies = ref<string[]>(['VTON', 'Edit (2 Ref)'])

/** 已选的 modelName 列表（默认只选指定模型） */
const selectedModelNames = ref<string[]>([
  'FastFit',
  'OmniTry',
  'Banana 1',
  'Banana Pro',
  'Seedream 4.0',
  'Seedream 4.5',
  'FLUX-2',
  'Qwen-Image-Edit-2509',
  'Qwen-Image-Edit-2511',
  'Ours (LoRA, 2 Ref)',
])

/** 筛选后的方法 stem 列表 */
const filteredMethodStems = computed(() => {
  return allMethodStems.filter(stem => {
    const meta = methodDict[stem]
    return (
      selectedStrategies.value.includes(meta.strategy) &&
      selectedModelNames.value.includes(meta.modelName)
    )
  })
})

/** 恢复默认筛选 */
const resetFilters = () => {
  selectedStrategies.value = ['VTON', 'Edit (2 Ref)']
  selectedModelNames.value = [
  'FastFit',
  'OmniTry',
  'Banana 1',
  'Banana Pro',
  'Seedream 4.0',
  'Seedream 4.5',
  'FLUX-2',
  'Qwen-Image-Edit-2509',
  'Qwen-Image-Edit-2511',
  'Ours (LoRA, 2 Ref)',
  ]
}

/** 全选所有方法 */
const selectAll = () => {
  selectedStrategies.value = [...ALL_STRATEGIES]
  selectedModelNames.value = [...new Set(allMethodStems.map(s => methodDict[s].modelName))]
}

// ─────────────────────────────────────────────
// 翻页逻辑（纯手动，无自动播放）
// ─────────────────────────────────────────────
const currentPage = ref(0)
const TOTAL_PAGES = computed(() => Math.max(1, comparisonIds.length))

const goToPrevPage = () => {
  currentPage.value = (currentPage.value - 1 + TOTAL_PAGES.value) % TOTAL_PAGES.value
}

const goToNextPage = () => {
  currentPage.value = (currentPage.value + 1) % TOTAL_PAGES.value
}

// ─────────────────────────────────────────────
// 当前页数据
// ─────────────────────────────────────────────
const currentEntry = computed(() => comparisonIds[currentPage.value])

// gt_test 可能是 .jpg 或 .png，优先尝试 .jpg，404 时自动回退 .png
const gtSrcOverride = ref<Record<string, string>>({})

const gtSrc = computed(() => {
  const id = currentEntry.value.id
  return gtSrcOverride.value[id] ?? `${baseUrl}results/${id}/garments/gt_test.jpg`
})

const onGtError = () => {
  const id = currentEntry.value.id
  const current = gtSrcOverride.value[id] ?? `${baseUrl}results/${id}/garments/gt_test.jpg`
  if (current.endsWith('.jpg')) {
    gtSrcOverride.value = { ...gtSrcOverride.value, [id]: `${baseUrl}results/${id}/garments/gt_test.png` }
  }
}

const garmentSrcs = computed(() => {
  const { id, garmentCount } = currentEntry.value
  return Array.from({ length: garmentCount }, (_, i) =>
    `${baseUrl}results/${id}/garments/garment_${i + 1}.jpg`
  )
})

type MethodItem = { stem: string; displayName: string; strategy: string; src: string }

const methodItems = computed<MethodItem[]>(() =>
  filteredMethodStems.value.map(stem => ({
    stem,
    displayName: methodDict[stem].displayName,
    strategy: methodDict[stem].strategy,
    src: `${baseUrl}results/${currentEntry.value.id}/inpainting-result/${stem}.png`,
  }))
)

/** 无选中方法（策略或 modelName 均为空） */
const noMethodSelected = computed(
  () => selectedStrategies.value.length === 0 || selectedModelNames.value.length === 0
)

// ─────────────────────────────────────────────
// 弹窗状态
// ─────────────────────────────────────────────
const modalVisible = ref(false)
const modalMethodName = ref('')
const modalMethodSrc = ref('')

const openModal = (item: MethodItem) => {
  modalMethodName.value = item.displayName
  modalMethodSrc.value = item.src
  modalVisible.value = true
}

const closeModal = () => {
  modalVisible.value = false
}

// ─────────────────────────────────────────────
// 筛选下拉框辅助
// ─────────────────────────────────────────────
const strategyDropdownOpen = ref(false)
const methodDropdownOpen = ref(false)

const toggleStrategy = (s: string) => {
  const idx = selectedStrategies.value.indexOf(s)
  if (idx >= 0) {
    selectedStrategies.value = selectedStrategies.value.filter(x => x !== s)
  } else {
    selectedStrategies.value = [...selectedStrategies.value, s]
  }
  // 策略变化时同步 modelName 选择（保留当前仍在选中策略内的 model）
  selectedModelNames.value = [
    ...new Set(
      allMethodStems
        .filter(stem => selectedStrategies.value.includes(methodDict[stem].strategy))
        .map(stem => methodDict[stem].modelName)
    )
  ]
}

const toggleModel = (name: string) => {
  const idx = selectedModelNames.value.indexOf(name)
  if (idx >= 0) {
    selectedModelNames.value = selectedModelNames.value.filter(x => x !== name)
  } else {
    selectedModelNames.value = [...selectedModelNames.value, name]
  }
}

/** 当前策略下所有唯一 modelName 列表（用于方法多选下拉） */
const availableModelNames = computed(() =>
  [
    ...new Set(
      allMethodStems
        .filter(stem => selectedStrategies.value.includes(methodDict[stem].strategy))
        .map(stem => methodDict[stem].modelName)
    )
  ]
)

const strategyLabel = computed(() => {
  if (selectedStrategies.value.length === 0) return 'Strategy: None'
  if (selectedStrategies.value.length === ALL_STRATEGIES.length) return 'Strategy: All'
  return 'Strategy: ' + selectedStrategies.value.join(', ')
})

const methodLabel = computed(() => {
  const total = availableModelNames.value.length
  const sel = selectedModelNames.value.length
  if (sel === 0) return 'Model: None'
  if (sel === total && total > 0) return 'Model: All'
  return `Model: ${sel} / ${total} selected`
})

// 点击外部关闭下拉
const onDocClick = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.cr-filter-dropdown')) {
    strategyDropdownOpen.value = false
    methodDropdownOpen.value = false
  }
}
onMounted(() => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
</script>

<template>
  <div class="cr-wrapper">
    <el-row justify="center">
      <el-col :xs="24" :sm="22" :md="20" :lg="18" :xl="16">

        <!-- ── 标题 ── -->
        <h2 class="cr-section-title">More Results</h2>

        <!-- ── 筛选栏 ── -->
        <div class="cr-filter-bar">
          <!-- 参考图策略多选下拉 -->
          <div class="cr-filter-dropdown" @click.stop>
            <button
              class="cr-filter-btn"
              type="button"
              @click="strategyDropdownOpen = !strategyDropdownOpen; methodDropdownOpen = false"
            >
              {{ strategyLabel }}
              <span class="cr-chevron">{{ strategyDropdownOpen ? '▲' : '▼' }}</span>
            </button>
            <div v-if="strategyDropdownOpen" class="cr-dropdown-panel">
              <label
                v-for="s in ALL_STRATEGIES"
                :key="s"
                class="cr-option"
                @click.stop="toggleStrategy(s)"
              >
                <input
                  type="checkbox"
                  :checked="selectedStrategies.includes(s)"
                  @change.stop="toggleStrategy(s)"
                />
                {{ s }}
              </label>
            </div>
          </div>

          <!-- 模型多选下拉（按 modelName 选择） -->
          <div class="cr-filter-dropdown" @click.stop>
            <button
              class="cr-filter-btn"
              type="button"
              @click="methodDropdownOpen = !methodDropdownOpen; strategyDropdownOpen = false"
            >
              {{ methodLabel }}
              <span class="cr-chevron">{{ methodDropdownOpen ? '▲' : '▼' }}</span>
            </button>
            <div v-if="methodDropdownOpen" class="cr-dropdown-panel cr-dropdown-panel--wide">
              <label
                v-for="name in availableModelNames"
                :key="name"
                class="cr-option"
                @click.stop="toggleModel(name)"
              >
                <input
                  type="checkbox"
                  :checked="selectedModelNames.includes(name)"
                  @change.stop="toggleModel(name)"
                />
                {{ name }}
              </label>
            </div>
          </div>

          <!-- 默认 / 全选按钮 -->
          <button class="cr-reset-btn" type="button" @click="resetFilters">Default</button>
          <button class="cr-all-btn" type="button" @click="selectAll">All</button>
        </div>

        <!-- ── 主体内容区（左：GT 固定；右：方法结果可滚动） ── -->
        <div class="cr-content">

          <!-- GT 图（左侧，固定，不参与滚动） -->
          <div class="cr-gt-col">
            <div class="cr-gt-wrapper">
              <Transition name="cr-fade" mode="out-in">
                <img :key="currentPage" class="cr-gt-img" :src="gtSrc" alt="GT" loading="lazy" @error="onGtError" />
              </Transition>
              <div class="cr-gt-badge">GT</div>
            </div>
            <div class="cr-method-name">Ground Truth</div>
          </div>

          <!-- 方法结果矩阵（右侧，固定高度，垂直滚动） -->
          <div class="cr-methods-col">
            <div v-if="methodItems.length === 0" class="cr-empty">
              {{
                noMethodSelected
                  ? 'No method selected. Please select methods from the filter above.'
                  : 'No methods match the current filter.'
              }}
            </div>
            <div v-else class="cr-methods-grid">
              <div
                v-for="item in methodItems"
                :key="item.stem"
                class="cr-method-cell"
                @click="openModal(item)"
              >
                <div class="cr-method-img-wrap">
                  <Transition name="cr-fade" mode="out-in">
                    <img
                      :key="`${item.stem}-${currentPage}`"
                      class="cr-method-img"
                      :src="item.src"
                      :alt="item.displayName"
                      loading="lazy"
                    />
                  </Transition>
                </div>
                <div class="cr-method-name">{{ item.displayName }}</div>
                <div class="cr-method-strategy-tag">{{ item.strategy }}</div>
              </div>
            </div>
          </div>

        </div>

        <!-- ── Garment 参考图一排 ── -->
        <div class="cr-garments-row">
          <div
            v-for="(src, idx) in garmentSrcs"
            :key="idx"
            class="cr-garment-cell"
          >
            <img class="cr-garment-img" :src="src" :alt="`garment_${idx + 1}`" loading="lazy" />
          </div>
        </div>

        <!-- ── 翻页控件 ── -->
        <div class="cr-controls">
          <button class="cr-nav-btn" type="button" @click="goToPrevPage">‹</button>
          <span class="cr-page-indicator">Page {{ currentPage + 1 }} / {{ TOTAL_PAGES }}</span>
          <button class="cr-nav-btn" type="button" @click="goToNextPage">›</button>
        </div>

      </el-col>
    </el-row>
  </div>

  <!-- ── 拖拽对比弹窗 ── -->
  <ComparisonModal
    :visible="modalVisible"
    :method-name="modalMethodName"
    :gt-src="gtSrc"
    :method-src="modalMethodSrc"
    @close="closeModal"
  />
</template>

<style scoped>
.cr-wrapper {
  margin-top: 24px;
  margin-bottom: 24px;
}

.cr-section-title {
  font-size: 28px;
  font-weight: 700;
  text-align: center;
  margin-bottom: 20px;
  color: #222222;
}

/* ── 筛选栏 ── */
.cr-filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.cr-filter-dropdown {
  position: relative;
}

.cr-filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  background: #ffffff;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  transition: border-color 0.15s, background 0.15s;
}

.cr-filter-btn:hover {
  border-color: #409eff;
  background: #f0f8ff;
}

.cr-chevron {
  font-size: 10px;
  color: #888;
}

.cr-reset-btn {
  display: inline-flex;
  align-items: center;
  padding: 5px 14px;
  border: 1px solid #e0584a;
  border-radius: 6px;
  background: #ffffff;
  color: #e0584a;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  transition: border-color 0.15s, background 0.15s, color 0.15s;
}

.cr-reset-btn:hover {
  background: #fff0ee;
}

.cr-all-btn {
  display: inline-flex;
  align-items: center;
  padding: 5px 14px;
  border: 1px solid #409eff;
  border-radius: 6px;
  background: #ffffff;
  color: #409eff;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  transition: border-color 0.15s, background 0.15s, color 0.15s;
}

.cr-all-btn:hover {
  background: #f0f8ff;
}

.cr-dropdown-panel {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 200;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  padding: 6px 0;
  min-width: 160px;
  max-height: 280px;
  overflow-y: auto;
}

.cr-dropdown-panel--wide {
  min-width: 220px;
}

.cr-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.1s;
}

.cr-option:hover {
  background: #f5f7fa;
}

.cr-option input[type='checkbox'] {
  width: 14px;
  height: 14px;
  cursor: pointer;
  accent-color: #409eff;
}

/* ── 渐变动画（仅作用于图像内容） ── */
.cr-fade-enter-active,
.cr-fade-leave-active {
  transition: opacity 0.3s ease;
}
.cr-fade-enter-from,
.cr-fade-leave-to {
  opacity: 0;
}

/* ── 主体内容（左右分栏，高度一致） ── */
.cr-content {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  max-height: calc(100vh - 280px);
}

/* GT 列：宽度与方法图一格一致，不参与滚动 */
.cr-gt-col {
  flex-shrink: 0;
  width: var(--cr-cell-width, 140px);
  position: sticky;
  top: 0;
}

.cr-gt-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 9 / 16;
  border-radius: 6px;
  overflow: hidden;
}

.cr-gt-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* GT badge（左上角） */
.cr-gt-badge {
  position: absolute;
  top: 4px;
  left: 4px;
  background: rgba(34, 34, 34, 0.72);
  color: #ffffff;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 999px;
  pointer-events: none;
  z-index: 2;
}

/* 方法矩阵列：垂直滚动 */
.cr-methods-col {
  flex: 1;
  min-width: 0;
  max-height: calc(100vh - 280px);
  overflow-y: auto;
}

/* 方法图网格列宽与 GT 列宽保持一致 */
.cr-methods-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, var(--cr-cell-width, 140px));
  gap: 10px;
}

.cr-empty {
  text-align: center;
  color: #999999;
  font-size: 13px;
  padding: 40px 0;
}

/* 窄屏优化：保证结果区至少两列，整体更紧凑 */
@media (max-width: 1024px) {
  .cr-gt-col {
    --cr-cell-width: 150px;
  }
  .cr-content {
    gap: 8px;
  }
}

@media (max-width: 500px) {
  .cr-gt-col {
    --cr-cell-width: 90px;
  }
  .cr-methods-grid {
    /* 至少两列，按可用宽度自适应收缩 */
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 6px;
  }
}

.cr-method-cell {
  cursor: pointer;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #ebebeb;
  transition: transform 0.15s, box-shadow 0.15s;
  background: #fafafa;
}

.cr-method-cell:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
}

.cr-method-img-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 9 / 16;
  overflow: hidden;
}

.cr-method-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.cr-method-name {
  font-size: 11px;
  color: #444444;
  text-align: center;
  padding: 4px 4px 2px;
  line-height: 1.3;
  word-break: break-word;
}

.cr-method-strategy-tag {
  font-size: 10px;
  color: #409eff;
  text-align: center;
  padding: 0 4px 6px;
  line-height: 1.2;
  white-space: nowrap;
}

/* ── Garment 参考图 ── */
.cr-garments-row {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.cr-garment-cell {
  width: 70px;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .cr-garment-cell {
    width: 52px;
  }
}

.cr-garment-img {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: contain;
  border-radius: 4px;
  border: 1px solid #ebebeb;
  display: block;
}

/* ── 翻页控件 ── */
.cr-controls {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 12px;
  color: #666666;
}

.cr-nav-btn {
  border: none;
  border-radius: 999px;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f2f2f2;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  transition: background 0.2s ease, transform 0.1s ease;
}

.cr-nav-btn:hover {
  background: #e0e0e0;
}

.cr-nav-btn:active {
  transform: scale(0.95);
}

.cr-page-indicator {
  min-width: 90px;
  text-align: center;
}
</style>
