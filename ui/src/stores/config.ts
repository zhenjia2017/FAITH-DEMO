// src/stores/config.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ConfigPayload = {
  selectedCheckboxTypes: string[]
  selectedRadioType1: string
  selectedRadioType2: string
  selectedRadioType3: string
  /** 0/1/2/3 iterations (default 1) */
  iteration: 0 | 1 | 2 | 3
  gnn_max_output_evidences: [number, number, number]
  /** Backend expects this mapped value */
  faith_or_unfaith: 'faith' | 'unfaith'
}

const MIN_VAL = 5
const MAX_VAL = 99

/** Stable defaults */
const DEFAULTS: Record<0 | 1 | 2 | 3, [number, number, number]> = {
  0: [5, 5, 5],
  1: [20, 5, 5],
  2: [50, 20, 5],
  3: [80, 60, 20],
}

/** clamp to [5, 99] and floor to int */
function clamp(v: number): number {
  const n = Math.floor(Number(v))
  if (!Number.isFinite(n)) return MIN_VAL
  return Math.max(MIN_VAL, Math.min(MAX_VAL, n))
}

/** Enforce strict descending only on first k editable items */
function fixEditableStrictDescending(arr: number[], k: number): number[] {
  const out = arr.map(clamp)
  for (let i = 1; i < k; i++) {
    if (!(out[i - 1] > out[i])) {
      out[i] = Math.max(MIN_VAL, Math.min(MAX_VAL, out[i - 1] - 1))
    }
  }
  return out
}

/** Number of editable boxes equals the iteration (0..3) */
function editableCount(it: 0 | 1 | 2 | 3): number {
  return it
}

export const useConfigStore = defineStore('config', () => {
  // ===== UI selections =====
  const selectedCheckboxTypes = ref<string[]>(['text', 'kb', 'table', 'info'])
  const selectedRadioType1    = ref<string>('ce')
  const selectedRadioType2    = ref<string>('explaignn') // kept in code; UI hidden by default
  const selectedRadioType3    = ref<string>('tiq')

  /** UI-facing switch: yes/no (default yes). Mapped to faith/unfaith in payload. */
  const temporalPruning = ref<'yes' | 'no'>('yes')

  /** Iterations (0..3), default 1 */
  const iteration = ref<0 | 1 | 2 | 3>(1)

  /**
   * Always maintain as length-3 number[], easy to index.
   * Initialize with defaults of iteration=1.
   */
  const gnnMaxOutputEvidences = ref<number[]>([...DEFAULTS[1]])

  /** Set iteration and reset evidences to stable defaults */
  function setIteration(n: number) {
    const it: 0 | 1 | 2 | 3 = (n === 0 || n === 1 || n === 2 || n === 3) ? n : 1
    iteration.value = it
    gnnMaxOutputEvidences.value = [...DEFAULTS[it]]
  }

  /**
   * Set evidences from UI: only override first k editable entries, others forced to 5.
   * Range and strict-desc fixes are applied automatically on editable part.
   */
  function setGnnEvidences(next: number[] | [number, number, number]) {
    const k = editableCount(iteration.value)
    const base = [...gnnMaxOutputEvidences.value]

    // override first k items
    for (let i = 0; i < k; i++) {
      const val = Array.isArray(next) ? next[i] : undefined
      base[i] = Number.isFinite(Number(val)) ? Number(val) : DEFAULTS[iteration.value][i]
    }

    // tail (non-editable) fixed to 5
    for (let i = k; i < 3; i++) base[i] = 5

    // apply strict descending on editable segment
    gnnMaxOutputEvidences.value = fixEditableStrictDescending(base, k)
  }

  /** Normalize current list (handy before payload) */
  function fixGnnList() {
    setGnnEvidences(gnnMaxOutputEvidences.value)
  }

  /** Build payload for backend (always 3 numbers + faith/unfaith mapping) */
  function toPayloadObject(): ConfigPayload {
    fixGnnList()
    const a = clamp(gnnMaxOutputEvidences.value[0] ?? 5)
    const b = clamp(gnnMaxOutputEvidences.value[1] ?? 5)
    const c = clamp(gnnMaxOutputEvidences.value[2] ?? 5)

    return {
      selectedCheckboxTypes:    selectedCheckboxTypes.value,
      selectedRadioType1:       selectedRadioType1.value,
      selectedRadioType2:       selectedRadioType2.value,
      selectedRadioType3:       selectedRadioType3.value,
      iteration:                iteration.value,
      gnn_max_output_evidences: [a, b, c] as [number, number, number], // << tuple assertion
      faith_or_unfaith:         temporalPruning.value === 'yes' ? 'faith' : 'unfaith',
    }
  }

  return {
    // state
    selectedCheckboxTypes,
    selectedRadioType1,
    selectedRadioType2,
    selectedRadioType3,
    temporalPruning,
    iteration,
    gnnMaxOutputEvidences,

    // actions
    setIteration,
    setGnnEvidences,
    fixGnnList,
    toPayloadObject,
  }
})
