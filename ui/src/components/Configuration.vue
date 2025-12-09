<template>
  <BContainer fluid>
    <!-- Header -->
    <div class="config-header" @click="toggleCollapse">
      <div class="w-100">
        <h5 class="title d-flex align-items-center mb-0">
          <i class="bi bi-gear" />
          Configuration & Example questions
          <i class="bi ms-auto" :class="isCollapsed ? 'bi-chevron-down' : 'bi-chevron-up'" />
        </h5>
        <p class="description">
          Configure the parameters for answering questions or choose an example question.
        </p>
      </div>
    </div>

    <!-- Body -->
    <transition name="collapse">
      <form v-show="!isCollapsed">
        <BRow class="align-items-stretch">
          <!-- Left: Configs -->
          <BCol cols="12" md="8">
            <div class="file-input-wrapper h-100">
              <!-- Information sources -->
              <div class="form-group">
                <h6 class="section-title">Information sources</h6>
                <div class="option-group">
                  <div class="form-check">
                    <input id="text" class="form-check-input" type="checkbox" value="text" v-model="selectedCheckboxTypes" />
                    <label class="form-check-label" for="text"><i class="bi-file-text-fill" /> Text</label>
                  </div>
                  <div class="form-check">
                    <input id="kb" class="form-check-input" type="checkbox" value="kb" v-model="selectedCheckboxTypes" />
                    <label class="form-check-label" for="kb"><i class="bi-database-fill" /> KB</label>
                  </div>
                  <div class="form-check">
                    <input id="table" class="form-check-input" type="checkbox" value="table" v-model="selectedCheckboxTypes" />
                    <label class="form-check-label" for="table"><i class="bi-table" /> Table</label>
                  </div>
                  <div class="form-check">
                    <input id="info" class="form-check-input" type="checkbox" value="info" v-model="selectedCheckboxTypes" />
                    <label class="form-check-label" for="info"><i class="bi-info-square-fill" /> Infobox</label>
                  </div>
                </div>
                <small v-if="infoSourceError" class="text-danger mt-1 d-block">{{ infoSourceError }}</small>
              </div>

              <!-- Evidence scoring -->
              <div class="form-group">
                <h6 class="section-title">Evidence scoring method</h6>
                <div class="option-group">
                  <div class="form-check">
                    <input id="ce" class="form-check-input" type="radio" value="ce" v-model="selectedRadioType1" />
                    <label class="form-check-label" for="ce">Cross Encoder</label>
                  </div>
                  <div class="form-check">
                    <input id="bm25" class="form-check-input" type="radio" value="bm25" v-model="selectedRadioType1" />
                    <label class="form-check-label" for="bm25">BM25</label>
                  </div>
                </div>
              </div>

              <!-- Iteration & evidences -->
              <div class="form-group">
                <h6 class="section-title">Graph reduction factors</h6>

                <!-- Iterations: 0 / 1 / 2 / 3 -->
                <div class="option-group mb-2">
                  <div class="fw-bold form-label d-block mb-1">No. of pruning iterations</div>
                  <div v-for="n in [0, 1, 2, 3]" :key="`iter-${n}`" class="form-check">
                    <input
                      :id="`iter-${n}`"
                      class="form-check-input"
                      type="radio"
                      :value="n"
                      v-model.number="iteration"
                    />
                    <label class="form-check-label" :for="`iter-${n}`">{{ n }}</label>
                  </div>
                </div>

                <!-- Evidences after pruning (dynamic inputs) -->
                <div v-if="iteration > 0">
                  <label class="fw-bold form-label d-block mb-1">No. of evidence after pruning</label>

                  <div
                    class="d-flex gap-2 align-items-start evidence-inputs"
                    @focusin="clearAllErrors" 
                    @click="clearAllErrors" 
                  >
                    <template v-for="(_, idx) in evidenceDrafts" :key="`einput-${idx}`">
                      <input
                        class="form-control"
                        :class="{ 'is-invalid': invalidFlags[idx] }"
                        type="number"
                        v-model.number="evidenceDrafts[idx]"
                        :min="MIN_VAL"
                        :max="MAX_VAL"
                        step="1"
                        @blur="commitEvidence(idx)"
                        @keydown.enter.prevent="commitEvidence(idx)"
                        @input="onInput(idx)"
                        :aria-invalid="invalidFlags[idx]"
                        style="max-width: 100px"
                      />
                      <span v-if="idx < evidenceDrafts.length - 1" class="mx-1 align-self-center">,</span>
                    </template>
                  </div>

                  <!-- Single, group-level error message (bottom only) -->
                  <div class="mt-1" v-if="groupErr">
                    <small class="text-danger">{{ groupErr }}</small>
                  </div>

                  <small class="text-muted d-block mt-2">
                    Minimum: 5 · Maximum: 99<br />
                    The number of evidence after pruning in each iteration should be smaller than in the previous iteration.
                  </small>
                </div>
              </div>

              <!-- Answering method (kept but hidden) -->
              <div class="form-group" v-show="showAnsweringMethod">
                <h6 class="section-title">Answering method</h6>
                <div class="option-group">
                  <div class="form-check">
                    <input id="explaignn" class="form-check-input" type="radio" value="explaignn" v-model="selectedRadioType2" />
                    <label class="form-check-label" for="explaignn">GNN</label>
                  </div>
                  <div class="form-check">
                    <input id="text_rag" class="form-check-input" type="radio" value="text_rag" v-model="selectedRadioType2" />
                    <label class="form-check-label" for="text_rag">RAG</label>
                  </div>
                  <div class="form-check">
                    <input id="graph_rag" class="form-check-input" type="radio" value="graph_rag" v-model="selectedRadioType2" />
                    <label class="form-check-label" for="graph_rag">Graph RAG</label>
                  </div>
                  <div class="form-check">
                    <input id="seq2seq_ha" class="form-check-input" type="radio" value="seq2seq_ha" v-model="selectedRadioType2" />
                    <label class="form-check-label" for="seq2seq_ha">Seq2Seq</label>
                  </div>
                </div>
              </div>

              <!-- Benchmarks -->
              <div class="form-group">
                <h6 class="section-title">Model trained via different benchmarks</h6>
                <div class="option-group">
                  <div class="form-check">
                    <input id="tiq" class="form-check-input" type="radio" value="tiq" v-model="selectedRadioType3" />
                    <label class="form-check-label" for="tiq">TIQ</label>
                  </div>
                  <div class="form-check">
                    <input id="timequestions" class="form-check-input" type="radio" value="timequestions" v-model="selectedRadioType3" />
                    <label class="form-check-label" for="timequestions">TimeQuestions</label>
                  </div>
                </div>
              </div>

              <!-- Temporal Pruning -->
              <div class="form-group">
                <h6 class="section-title">Temporal pruning</h6>
                <div class="option-group">
                  <div class="form-check">
                    <input
                      id="tp-yes"
                      class="form-check-input"
                      type="radio"
                      value="yes"
                      v-model="temporalPruning"
                    />
                    <label class="form-check-label" for="tp-yes">Yes</label>
                  </div>
                  <div class="form-check">
                    <input
                      id="tp-no"
                      class="form-check-input"
                      type="radio"
                      value="no"
                      v-model="temporalPruning"
                    />
                    <label class="form-check-label" for="tp-no">No</label>
                  </div>
                </div>
              </div>

            </div>
          </BCol>

          <!-- Right: Example questions -->
          <BCol cols="12" md="4" class="d-flex flex-column" style="min-height:0">
            <div class="example-questions flex-fill d-flex flex-column">
              <div class="eq-header">Example questions</div>
              <ul class="eq-list">
                <li v-for="q in exampleList" :key="q" @click="selectExample(q)">{{ q }}</li>
              </ul>
            </div>
          </BCol>
        </BRow>
      </form>
    </transition>
  </BContainer>
</template>

<script setup lang="ts">
/* =========================
   Imports
========================= */
import { BContainer, BRow, BCol } from 'bootstrap-vue-3'
import { ref, computed, watch, withDefaults, defineProps, onMounted, nextTick } from 'vue'
import { defineEmits } from 'vue'
import { useConfigStore } from '@/stores/config'
import type { ConfigPayload } from '@/stores/config'

/* =========================
   Setup & Store
========================= */
withDefaults(defineProps<{ msg?: string }>(), { msg: '' })
const emit = defineEmits<{
  (e: 'config-changed', cfg: ConfigPayload): void
  (e: 'example-selected', question: string): void
}>()
function commitAllEvidences() {
  for (let i = 0; i < evidenceDrafts.value.length; i++) {
    commitEvidence(i)
  }
}

// Expose
defineExpose({ commitAllEvidences })
const configStore = useConfigStore()
const showAnsweringMethod = ref(false)
const isCollapsed = ref(false)
function toggleCollapse() { isCollapsed.value = !isCollapsed.value }

/* =========================
   Bindings (Pinia <-> UI)
========================= */
const selectedCheckboxTypes = computed({
  get: () => configStore.selectedCheckboxTypes,
  set: (v) => { configStore.selectedCheckboxTypes = v }
})
const selectedRadioType1 = computed({
  get: () => configStore.selectedRadioType1,
  set: (v) => { configStore.selectedRadioType1 = v }
})
const selectedRadioType2 = computed({
  get: () => configStore.selectedRadioType2,
  set: (v) => { configStore.selectedRadioType2 = v }
})
const selectedRadioType3 = computed({
  get: () => configStore.selectedRadioType3,
  set: (v) => { configStore.selectedRadioType3 = v }
})

const iteration = computed<number>({
  get: () => {
    const v = Number(configStore.iteration)
    return [0, 1, 2, 3].includes(v) ? v : 1
  },
  set: (n) => { configStore.setIteration(Number(n)) }
})

/* =========================
   Evidence controls
========================= */
const MIN_VAL = 5
const MAX_VAL = 99

const DEFAULTS: Record<number, number[]> = {
  0: [],
  1: [20],
  2: [50, 20],
  3: [80, 60, 20],
}

function clearAllErrors() {
  // 清除整组错误提示
  groupErr.value = ''
  // 把每个输入框的标红全部去掉（长度与当前 inputs 数量一致）
  invalidFlags.value = Array(evidenceDrafts.value.length).fill(false)
}

const evidenceDrafts = ref<number[]>([])
const lastGoodDrafts = ref<number[]>([])
const groupErr       = ref<string>('')

/** NEW: per-field invalid flags, only mark the wrong input red */
const invalidFlags   = ref<boolean[]>([])

function isStrictDescending(arr: number[]): boolean {
  for (let i = 0; i < arr.length - 1; i++) {
    if (!(arr[i] > arr[i + 1])) return false
  }
  return true
}
// 默认 Yes；若 store 未定义，get 时回退到 'yes'
const temporalPruning = computed<'yes' | 'no'>({
  get: () => (configStore as any).temporalPruning ?? 'yes',
  set: (v) => { (configStore as any).temporalPruning = v }
})

function seedDraftsByIteration(it: number) {
  const desired = DEFAULTS[it] ? [...DEFAULTS[it]] : []
  evidenceDrafts.value = desired
  lastGoodDrafts.value = [...desired] // snapshot for revert
  groupErr.value       = ''
  invalidFlags.value   = Array(desired.length).fill(false)
}

/** Clear error highlights when typing in a specific input */
function onInput(idx: number) {
  invalidFlags.value[idx] = false
  groupErr.value = ''
}

/** Validate only on blur/enter. If invalid, revert to lastGood and show a single group-level message. */
function commitEvidence(idx: number) {
  // 1) Range check
  const val = Number(evidenceDrafts.value[idx])
  if (!Number.isFinite(val) || val < MIN_VAL || val > MAX_VAL) {
    const prev = lastGoodDrafts.value[idx]
    groupErr.value = `Value must be between ${MIN_VAL} and ${MAX_VAL}.`
    evidenceDrafts.value[idx] = prev
    invalidFlags.value[idx] = true
    return
  }

  // 2) Strictly decreasing check (left > right)
  if (evidenceDrafts.value.length > 1 && !isStrictDescending(evidenceDrafts.value)) {
    const prev = lastGoodDrafts.value[idx]
    groupErr.value = `Values must be strictly decreasing (left > right).`
    evidenceDrafts.value[idx] = prev
    invalidFlags.value[idx] = true
    return
  }

  // 3) Valid -> update snapshot, write to store, emit (dedup)
  invalidFlags.value[idx] = false
  lastGoodDrafts.value = [...evidenceDrafts.value]
  configStore.setGnnEvidences([...evidenceDrafts.value])
  emitIfChanged()
}

/* =========================
   Dedupe emit
========================= */
const lastPayloadJSON = ref<string>('')
function emitIfChanged() {
  const nextObj  = configStore.toPayloadObject()
  const nextJSON = JSON.stringify(nextObj)
  if (nextJSON !== lastPayloadJSON.value) {
    lastPayloadJSON.value = nextJSON
    emit('config-changed', nextObj)
  }
}
onMounted(() => {
  const it = iteration.value
  const need = it // 可编辑框数量 = iteration

  const fromStore = Array.isArray(configStore.gnnMaxOutputEvidences)
    ? configStore.gnnMaxOutputEvidences.slice(0, need)
    : []

  // 若 store 里已有用户改过的值，则优先使用；否则用该 iteration 的默认
  const desired =
    (fromStore.length === need && fromStore.every(v => Number.isFinite(v)))
      ? fromStore
      : DEFAULTS[it].slice(0, need)

  evidenceDrafts.value = desired
  lastGoodDrafts.value = [...desired]
  groupErr.value = ''
  invalidFlags.value = Array(desired.length).fill(false)
})
/* =========================
   Watchers
========================= */
watch(
  () => iteration.value,
  (it) => {
    // 用户手动切换 iteration 时，按产品规则载入该档位默认并写回 store
    seedDraftsByIteration(it) // 这里会用 DEFAULTS[it]
    configStore.setGnnEvidences([...evidenceDrafts.value])
    emitIfChanged()
  },
  { immediate: false } 
)

watch(
  () => configStore.gnnMaxOutputEvidences,
  (arr) => {
    const need = DEFAULTS[iteration.value]?.length ?? 0
    if (Array.isArray(arr) && arr.length === 3) {
      const nextDraft = arr.slice(0, need)
      const same = nextDraft.length === evidenceDrafts.value.length
        && nextDraft.every((v, i) => v === evidenceDrafts.value[i])
      if (!same) {
        evidenceDrafts.value = nextDraft
        lastGoodDrafts.value = [...nextDraft]
        groupErr.value = ''
        invalidFlags.value = Array(need).fill(false)
      }
    }
  },
  { deep: true }
)

watch(
  [selectedCheckboxTypes, selectedRadioType1, selectedRadioType2, selectedRadioType3, temporalPruning],
  () => emitIfChanged(),
  { deep: true }
)

/* =========================
   Examples
========================= */
const exampleList = [
  "What award did Sarah Vaughan receive when she was given the Grammy Lifetime Achievement Award?",
  "Who was Katharine Hepburn's partner before she won the Academy Award for Best Actress for her performance in Guess Who's Coming to Dinner? ",
  "Which university did Thomas Hunt Morgan attend after receiving his Bachelor of Science degree?",
  "At what place was Mikhail Skobelev educated in 1861?",
  "What position was Cyril Ramaphosa held in the year 2018?",
  "Which baseball team did Tony Taylor play for before the Philadelphia Phillies?"
]
function selectExample(q: string) { emit('example-selected', q) }


// 全部可选项
const ALL_SOURCES = ['text', 'kb', 'table', 'info'] as const

// 错误信息 & 抑制一次性清除的标记
const infoSourceError = ref('')
const suppressClearOnce = ref(false)

// 初始检测：若为空则强制全选并提示（提示保留 2.5s）
onMounted(() => {
  const arr = selectedCheckboxTypes.value ?? []
  if (!Array.isArray(arr) || arr.length === 0) {
    infoSourceError.value = 'At least one information source is required. All sources have been selected for you.'
    suppressClearOnce.value = true
    selectedCheckboxTypes.value = [...ALL_SOURCES]
    emitIfChanged()
    // 延迟清除提示
    setTimeout(() => {
      infoSourceError.value = ''
      suppressClearOnce.value = false
    }, 2500)
  } else {
    infoSourceError.value = ''
  }
})

// 监听 sources 变化：清空时提示并全选（同样保留 2.5s）
watch(
  () => selectedCheckboxTypes.value,
  (arr) => {
    const len = Array.isArray(arr) ? arr.length : 0
    if (len === 0) {
      nextTick(() => {
        infoSourceError.value = 'At least one information source is required. All sources have been selected for you.'
        suppressClearOnce.value = true
        selectedCheckboxTypes.value = [...ALL_SOURCES]
        emitIfChanged()
        setTimeout(() => {
          infoSourceError.value = ''
          suppressClearOnce.value = false
        }, 2500)
      })
    } else {
      // 只有在不是“自动修复”的下一拍，才清除提示
      if (!suppressClearOnce.value) {
        infoSourceError.value = ''
      } else {
        // 自动修复后的第一轮变更，保留提示但关闭抑制标志
        suppressClearOnce.value = false
      }
    }
  }
)


</script>

<style scoped>
/* Wrapper */
.file-input-wrapper { 
  padding: 20px; 
  background-color: #f9f9f9; 
  border-radius: 8px; 
  box-shadow: 0 0 10px rgba(0,0,0,.1); 
}
.config-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  cursor: pointer; 
}

/* Collapse transition */
.collapse-enter-active,.collapse-leave-active { 
  transition: max-height .3s ease, opacity .3s ease; 
}
.collapse-enter-from,.collapse-leave-to { 
  max-height: 0; 
  opacity: 0; 
  overflow: hidden; 
}
.collapse-enter-to,.collapse-leave-from { 
  max-height: 1000px; 
  opacity: 1; 
}

/* Title / Desc */
.title { 
  width: 100%; 
  font-weight: bold; 
  font-size: 24px; 
  color: #333; 
  margin-bottom: 10px; 
  background-color: #eaeaea; 
  padding: 5px 10px; 
  border-radius: 4px; 
}
.description { 
  font-size: 14px; 
  color: #666; 
  margin-bottom: 20px; 
}

/* Groups */
.form-group { 
  margin-bottom: 20px; 
  padding: 15px; 
  border-bottom: 1px solid #eee; 
  box-shadow: 0 2px 5px rgba(0,0,0,.05); 
}
.section-title { 
  font-weight: bold; 
  font-size: 18px; 
  color: #444; 
  margin-bottom: 10px; 
}
.option-group { 
  display: flex; 
  flex-wrap: wrap; 
  gap: 15px; 
}
.form-check { 
  display: flex; 
  align-items: center; 
}
.form-check-input { 
  margin-right: 8px; 
}
.form-check-label { 
  display: inline-block; 
  padding: 4px 12px; 
  border: 2px solid #000; 
  border-radius: 6px; 
  background: #fff; 
  color: #000; 
  font-size: 14px; 
  line-height: 1; 
  white-space: nowrap; 
}
.bi { 
  margin-right: 5px; 
  font-size: 16px; 
  transition: color .3s; 
}
.form-check-input:checked + .form-check-label .bi { 
  color: #007bff; 
}

/* Example list */
.example-questions { 
  background: #8b95a1; 
  border-radius: 6px; 
  overflow: hidden; 
  font-family: sans-serif; 
  display: flex; 
  flex-direction: column; 
  min-height: 0;
}
.eq-header { 
  flex-shrink: 0; 
  background: #5d666e; 
  color: #fff; 
  font-weight: bold; 
  padding: 1rem 2rem; 
  font-size: 1.2rem; 
  flex: 0 0 auto;
}
.eq-list { 
  flex: 1 1 0%;
  list-style: none; 
  margin: 0; 
  padding: 0 20px; 
  min-height: 0;
  max-height: 600px;
  overflow-y: auto; 
}
.eq-list li { 
  position: relative; 
  padding: 22px 15px; 
  color: #fff; 
  cursor: pointer; 
  transition: background-color .2s ease; 
}
.eq-list li + li::before { 
  content: ""; 
  position: absolute; 
  top: 0; left: 1rem; 
  right: 1rem; 
  height: 1px; 
  background: rgba(255,255,255,.3); 
}
.eq-list li:hover { 
  background: rgba(0,0,0,.1); 
}
.eq-list::-webkit-scrollbar { 
  width: 8px; 
}
.eq-list::-webkit-scrollbar-thumb { 
  background: rgba(0,0,0,.2); 
  border-radius: 4px; 
}
.eq-list::-webkit-scrollbar-track { 
  background: transparent; 
}

/* Inputs row */
.evidence-inputs { 
  flex-wrap: wrap; 
}
</style>
