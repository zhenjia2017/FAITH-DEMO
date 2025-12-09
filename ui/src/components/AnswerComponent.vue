<template>
  <div class="input-wrapper" ref="wrapperRef">
    <div class="input-area">
      <input
        type="text"
        placeholder="Please enter your question here"
        v-model="questionInput"
        class="form-control"
        @keyup.enter="handleQuestionAnswer"
        @focus="showDropdown"
      />
    </div>

    <!-- History -->
    <ul class="history-list" v-show="isDropdownVisible && history.length">
      <li
        v-for="(q, i) in history"
        :key="i"
        @mousedown.prevent="selectHistory(q)"
      >
        {{ q }}
      </li>
    </ul>

    <!-- Answer status -->
    <div class="answer-status mt-2" v-if="answerStatus">
      <div
        :class="[
          'alert',
          answerStatus.type === 'error' ? 'alert-danger' : 'alert-info',
          'mb-0',
          'py-2'
        ]"
      >
        <i
          :class="[
            'bi',
            answerStatus.type === 'error' ? 'bi-exclamation-triangle' : 'bi-info-circle',
            'me-2'
          ]"
        ></i>
        {{ answerStatus.message }}
      </div>
    </div>
  </div>

  <!-- Configuration Card -->
  <BCard class="mt-4 mb-4 no-hover">
    <Configuration
      ref="configRef"
      @example-selected="onExampleSelected"
      @config-changed="handleConfigChanged"
    />
  </BCard>

  <div class="text-center mt-4">
    <button
      class="btn btn-primary w-100"
      @click="handleQuestionAnswer"
      :disabled="isAnswering"
    >
      <span v-if="!isAnswering">
        <i class="bi bi-chat-dots me-1"></i>
        Answer
      </span>
      <span v-else>
        <span
          class="spinner-border spinner-border-sm me-1"
          role="status"
          aria-hidden="true"
        ></span>
        Answering...
      </span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useStorage, onClickOutside } from '@vueuse/core'
import { useRouter, useRoute } from 'vue-router'
import { BCard } from 'bootstrap-vue-3'
import Configuration from '../components/Configuration.vue'
import { useConfigStore } from '@/stores/config'
import type { ConfigPayload } from '@/stores/config'

/** ========== Props & Emits ========== */
const props = defineProps<{ initialQuestion?: string }>()
const emit = defineEmits<{ (e: 'question-submitted', question: string): void }>()

/** ========== Local State ========== */
const questionInput = ref('')
const answerStatus  = ref<{ type: 'error' | 'info'; message: string } | null>(null)
const isAnswering   = ref(false)

const router = useRouter()
const route  = useRoute()

/** Watch initial question */
watch(
  () => props.initialQuestion,
  (q) => {
    if (q && q !== questionInput.value) {
      questionInput.value = q
      handleQuestionAnswer()
    }
  }
)

/** ========== History dropdown ========== */
const history = useStorage<string[]>('questionHistory', [])

const isDropdownVisible = ref(false)
const wrapperRef = ref<HTMLElement | null>(null)
function showDropdown() { isDropdownVisible.value = true }
onClickOutside(wrapperRef, () => { isDropdownVisible.value = false })
function selectHistory(q: string) {
  questionInput.value = q
  isDropdownVisible.value = false
}

/** ========== Store ========== */
const configStore = useConfigStore()

type ConfigExposed = { commitAllEvidences?: () => void }
const configRef = ref<ConfigExposed | null>(null)

function eqArr<T>(a: T[] = [], b: T[] = []) {
  return a.length === b.length && a.every((v, i) => v === b[i])
}

/** ========== Main: Answer ========== */
async function handleQuestionAnswer() {
  const q = questionInput.value.trim()
  if (!q) {
    answerStatus.value = { type: 'error', message: 'Please enter a question' }
    return
  }

  // 更新历史
  history.value = [q, ...history.value.filter(item => item !== q)].slice(0, 10)

  // 若不在 Guide，先跳转
  if (route.name !== 'Guide') {
    await router.push({ name: 'Guide', query: { APPquestion: q } })
    return
  }

  isAnswering.value = true
  answerStatus.value = { type: 'info', message: 'Analyzing question...' }

  try {
    // 关键：统一提交配置面板里的输入（即使仍在 focus）
    configRef.value?.commitAllEvidences?.()
    await nextTick()

    // 双保险：强制 blur 当前活动元素，让其触发 onBlur 写回
    const active = document.activeElement as HTMLElement | null
    if (active && typeof active.blur === 'function') active.blur()
    await new Promise((r) => requestAnimationFrame(() => r(null)))
    await nextTick()

    // 读取 Pinia（已是最新值）
    const cfgPayload = configStore.toPayloadObject()

    const bodyData = {
      question:  q,
      es_method: cfgPayload.selectedRadioType1,
      ha_method: cfgPayload.selectedRadioType2,
      benchmark: cfgPayload.selectedRadioType3,
      sources:   cfgPayload.selectedCheckboxTypes.join('_'),
      iteration: cfgPayload.iteration,
      gnn_max_output_evidences: cfgPayload.gnn_max_output_evidences,
      faith_or_unfaith: cfgPayload.faith_or_unfaith,
    }

    const response = await fetch('/api/process-question', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyData)
    })

    if (!response.ok) {
      // 尝试读取后端的错误信息
      let msg = 'Failed to process question'
      try {
        const errJson = await response.json()
        msg = errJson?.error || errJson?.message || msg
      } catch { /* ignore */ }
      throw new Error(msg)
    }

    const result = await response.json()
    emit('question-submitted', q)
    sessionStorage.setItem('qa_result', JSON.stringify(result))
    await router.replace({ name: 'Faith' })
  } catch (err: any) {
    console.error(err)
    answerStatus.value = { type: 'error', message: err?.message || 'Error answering question' }
  } finally {
    isAnswering.value = false
  }
}

/** 示例问题选择 */
function onExampleSelected(q: string) {
  questionInput.value = q
}

/** ========== 接收配置变更（去重写回 Store，避免循环） ========== */
function handleConfigChanged(newConfig: ConfigPayload) {
  if (!eqArr(configStore.selectedCheckboxTypes, newConfig.selectedCheckboxTypes)) {
    configStore.selectedCheckboxTypes = [...newConfig.selectedCheckboxTypes]
  }
  if (configStore.selectedRadioType1 !== newConfig.selectedRadioType1) {
    configStore.selectedRadioType1 = newConfig.selectedRadioType1
  }
  if (configStore.selectedRadioType2 !== newConfig.selectedRadioType2) {
    configStore.selectedRadioType2 = newConfig.selectedRadioType2
  }
  if (configStore.selectedRadioType3 !== newConfig.selectedRadioType3) {
    configStore.selectedRadioType3 = newConfig.selectedRadioType3
  }

  if (newConfig.iteration !== undefined && newConfig.iteration !== configStore.iteration) {
    configStore.setIteration(newConfig.iteration)
  }

  if (Array.isArray(newConfig.gnn_max_output_evidences)) {
    const cur = [...configStore.gnnMaxOutputEvidences]
    if (!eqArr(cur, newConfig.gnn_max_output_evidences)) {
      configStore.setGnnEvidences(newConfig.gnn_max_output_evidences)
    }
  }
}
</script>

<style scoped>
.input-wrapper { position: relative; }

/* 下拉菜单 */
.history-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin: 0;
  padding: 0;
  list-style: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  background: #fff;
  z-index: 10;
}
.history-list li { padding: 0.5rem; cursor: pointer; }
.history-list li:hover { background: #f0f0f0; }

/* 输入区域 */
.input-area {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 1rem;
}
.form-control {
  flex: 1;
  padding: 0.75rem;
  font-size: 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  transition: border-color .3s ease;
}
.form-control:focus {
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, .1);
  outline: none;
}

/* 按钮 */
.btn-primary {
  padding: .75rem 1.5rem;
  font-size: 1rem;
  border-radius: 8px;
  background: #4299e1;
  border: none;
  transition: background-color .3s ease;
}
.btn-primary:hover:not(:disabled) { background: #2b6cb0; }
.btn-primary:disabled { background: #90cdf4; cursor: not-allowed; }

/* 状态条 */
.answer-status { border-radius: 8px; overflow: hidden; }
.alert { margin: 0; display: flex; align-items: center; }
.alert i { font-size: 1.2rem; }

/* 响应式 */
@media (max-width: 768px) {
  .input-area { flex-direction: column; }
  .btn-primary { width: 100%; }
}

/* 去除卡片 hover 效果 */
.no-hover { transition: none !important; box-shadow: none !important; }
.no-hover:hover { box-shadow: none !important; transform: none !important; }
</style>
