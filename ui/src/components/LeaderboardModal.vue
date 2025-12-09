<template>
  <BModal
    v-model="modelValue"
    title="Leaderboard"
    size="lg"
    centered
    @hide="handleClose"
  >
    <div class="leaderboard-scroll">
      <!-- ===== TIQ ===== -->
      <h5 class="headline-text">TIQ</h5>
      <div class="table-responsive">
        <table class="table table-striped leaderboard-table">
          <!-- unified column widths for both tables -->
          <colgroup>
            <col style="width:48%" />
            <col style="width:17%" />
            <col style="width:17%" />
            <col style="width:18%" />
          </colgroup>
          <thead>
            <tr>
              <th class="sticky">Method</th>
              <th class="sticky text-end">P@1</th>
              <th class="sticky text-end">MRR</th>
              <th class="sticky text-end">Hit@5</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in tiqRows" :key="`tiq-${i}`" :class="{ 'top-row': i === 0 }">
              <td class="method-cell">
                <strong>{{ r.method }}</strong>
                <a v-if="r.citation" class="paper-link" :href="r.citation.url" target="_blank" rel="noopener">
                  {{ r.citation.text }}
                </a>
              </td>
              <td class="num" :class="metricClass(r.p1, tiqMax.p1)">{{ fmt(r.p1) }}</td>
              <td class="num" :class="metricClass(r.mrr, tiqMax.mrr)">{{ fmt(r.mrr) }}</td>
              <td class="num" :class="metricClass(r.hit5, tiqMax.hit5)">{{ fmt(r.hit5) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <hr class="separator" />

      <!-- ===== TimeQuestions ===== -->
      <h5 class="headline-text">TimeQuestions</h5>
      <div class="table-responsive">
        <table class="table table-striped leaderboard-table">
          <!-- same colgroup as above to keep layout identical -->
          <colgroup>
            <col style="width:48%" />
            <col style="width:17%" />
            <col style="width:17%" />
            <col style="width:18%" />
          </colgroup>
          <thead>
            <tr>
              <th class="sticky">Method</th>
              <th class="sticky text-end">P@1</th>
              <th class="sticky text-end">MRR</th>
              <th class="sticky text-end">Hit@5</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in tqRows" :key="`tq-${i}`" :class="{ 'top-row': i === 0 }">
              <td class="method-cell">
                <strong>{{ r.method }}</strong>
                <a v-if="r.citation" class="paper-link" :href="r.citation.url" target="_blank" rel="noopener">
                  {{ r.citation.text }}
                </a>
              </td>
              <td class="num" :class="metricClass(r.p1, tqMax.p1)">{{ fmt(r.p1) }}</td>
              <td class="num" :class="metricClass(r.mrr, tqMax.mrr)">{{ fmt(r.mrr) }}</td>
              <td class="num" :class="metricClass(r.hit5, tqMax.hit5)">{{ fmt(r.hit5) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <template #footer>
      <BButton variant="secondary" @click="handleClose">Close</BButton>
    </template>
  </BModal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { BButton } from 'bootstrap-vue-3'

type Row = {
  method: string
  citation?: { text: string; url: string }
  p1?: number | null
  mrr?: number | null
  hit5?: number | null
}

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits(['update:modelValue', 'close'])

const modelValue = computed({
  get: () => props.modelValue,
  set: (v: boolean) => {
    emit('update:modelValue', v)
    if (!v) emit('close')
  },
})
const handleClose = () => {
  emit('update:modelValue', false)
  emit('close')
}

/* ---- Data (keep both tables in the same shape) ---- */
const tiqRows: Row[] = [
  { method: 'FAITH',       citation: { text: "Jia et al. ’24", url: 'https://arxiv.org/abs/2402.15400' }, p1: 0.491, mrr: 0.603, hit5: 0.752 },
  { method: 'EXPLAIGNN',   citation: { text: "Christmann et al. ’23", url: 'https://arxiv.org/abs/2305.01548' }, p1: 0.446, mrr: 0.584, hit5: 0.765 },
  { method: 'UniK-QA',     citation: { text: "Oğuz et al. ’22", url: 'https://aclanthology.org/2022.findings-naacl.115/' },       p1: 0.425, mrr: 0.480, hit5: 0.540 },
  { method: 'GPT-4',       citation: { text: "OpenAI ’23", url: 'https://arxiv.org/abs/2303.08774' },            p1: 0.286, mrr: null,  hit5: null  },
  { method: 'InstructGPT', citation: { text: "Ouyang et al. ’22", url: 'https://papers.nips.cc/paper_files/paper/2022/hash/b1efde53be364a73914f58805a001731-Abstract-Conference.html' },     p1: 0.236, mrr: null,  hit5: null  },
  { method: 'UNIQORN',     citation: { text: "Pramanik et al. ’21", url: 'https://arxiv.org/abs/2108.08614' },   p1: 0.237, mrr: 0.255, hit5: 0.277 },
  { method: 'EXAQT',       citation: { text: "Jia et al. ’21", url: 'https://dl.acm.org/doi/10.1145/3459637.3482416' },        p1: 0.232, mrr: 0.378, hit5: 0.587 },
  { method: 'TempoQR',     citation: { text: "Mavromatis et al. ’22", url: 'https://aaai.org/papers/05825-tempoqr-temporal-question-reasoning-over-knowledge-graphs/' }, p1: 0.011, mrr: 0.018, hit5: 0.022 },
  { method: 'CRONKGQA',    citation: { text: "Saxena et al. ’21", url: 'https://aclanthology.org/2021.acl-long.520/' },     p1: 0.006, mrr: 0.011, hit5: 0.014 },
]

const tqRows: Row[] = [
  { method: 'TimeR4',      citation: { text: "Qian et al. ’24", url: 'https://aclanthology.org/2024.emnlp-main.394/' },       p1: 0.781, mrr: null,  hit5: null  },
  { method: 'QUASAR',      citation: { text: "Christmann & Weikum ’24", url: 'https://arxiv.org/pdf/2412.07420' }, p1: 0.754, mrr: 0.778, hit5: 0.791 },
  { method: 'TwiRGCN',     citation: { text: "Sharma et al. ’23", url: 'https://aclanthology.org/2023.eacl-main.150/' },     p1: 0.605, mrr: null,  hit5: null  },
  { method: 'EXAQT',       citation: { text: "Jia et al. ’21", url: 'https://dl.acm.org/doi/10.1145/3459637.3482416' },        p1: 0.565, mrr: 0.599, hit5: 0.664 },
  { method: 'SF-TQA',      citation: { text: "Ding et al. ’22", url: 'https://arxiv.org/abs/2210.04490' },       p1: 0.539, mrr: null,  hit5: null  },
  { method: 'FAITH',       citation: { text: "Jia et al. ’24", url: 'https://arxiv.org/abs/2402.15400' }, p1: 0.535, mrr: 0.582, hit5: 0.635 },
  { method: 'LGQA',        citation: { text: "Liu et al. ’23", url: 'https://www.ijcai.org/proceedings/2023/0571.pdf' },        p1: 0.529, mrr: null,  hit5: null  },
  { method: 'EXPLAIGNN',   citation: { text: "Christmann et al. ’23", url: 'https://arxiv.org/abs/2305.01548' }, p1: 0.525, mrr: 0.587, hit5: 0.673 },
  { method: 'CTRN',        citation: { text: "Jiao et al. ’23", url: 'https://link.springer.com/article/10.1007/s10489-022-03913-6' },       p1: 0.465, mrr: null,  hit5: null  },
  { method: 'GRAFT-Net',   citation: { text: "Sun et al. ’18", url: 'https://arxiv.org/abs/1809.00782' },        p1: 0.452, mrr: 0.485, hit5: 0.554 },
  { method: 'TempoQR',     citation: { text: "Mavromatis et al. ’22", url: 'https://aaai.org/papers/05825-tempoqr-temporal-question-reasoning-over-knowledge-graphs/' }, p1: 0.438, mrr: 0.465, hit5: 0.488 },
  { method: 'TMA',         citation: { text: "Liu et al. ’23", url: 'https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=10095395' },        p1: 0.436, mrr: null,  hit5: null  },
  { method: 'UniK-QA',     citation: { text: "Oğuz et al. ’22", url: 'https://aclanthology.org/2022.findings-naacl.115/' },       p1: 0.424, mrr: 0.453, hit5: 0.486 },
  { method: 'Convinse',    citation: { text: "Christmann et al. ’22", url: 'https://dl.acm.org/doi/pdf/10.1145/3477495.3531815/' }, p1: 0.423, mrr: null,  hit5: null  },
  { method: 'CRONKGQA',    citation: { text: "Saxena et al. ’21", url: 'https://aclanthology.org/2021.acl-long.520/' },     p1: 0.395, mrr: 0.423, hit5: 0.450 },
  { method: 'UNIQORN',     citation: { text: "Pramanik et al. ’21", url: 'https://arxiv.org/abs/2108.08614' },   p1: 0.331, mrr: 0.409, hit5: 0.538 },
  { method: 'GPT-4',       citation: { text: "OpenAI ’23", url: 'https://arxiv.org/abs/2303.08774' },            p1: 0.306, mrr: null,  hit5: null  },
  { method: 'InstructGPT', citation: { text: "Ouyang et al. ’22", url: 'https://papers.nips.cc/paper_files/paper/2022/hash/b1efde53be364a73914f58805a001731-Abstract-Conference.html' },     p1: 0.224, mrr: null,  hit5: null  },
  { method: 'Llama3',      citation: { text: "Touvron et al. ’23", url: 'https://arxiv.org/pdf/2302.13971' },    p1: 0.178, mrr: null,  hit5: null  },
  { method: 'PullNet',     citation: { text: "Sun et al. ’19", url: 'https://arxiv.org/abs/1904.09537' },        p1: 0.105, mrr: 0.136, hit5: 0.186 },
]

/* ---- Helpers: get per-column max, format cells, bold the maxima ---- */
const maxOf = (rows: Row[], key: 'p1' | 'mrr' | 'hit5') =>
  Math.max(...rows.map(r => (typeof r[key] === 'number' ? (r[key] as number) : -Infinity)))

const tiqMax = { p1: maxOf(tiqRows, 'p1'), mrr: maxOf(tiqRows, 'mrr'), hit5: maxOf(tiqRows, 'hit5') }
const tqMax  = { p1: maxOf(tqRows,  'p1'), mrr: maxOf(tqRows,  'mrr'), hit5: maxOf(tqRows,  'hit5') }

const fmt = (v?: number | null) => (typeof v === 'number' ? v.toFixed(3) : '---')
const metricClass = (v: number | null | undefined, max: number) =>
  typeof v === 'number' && v === max ? 'cell-strong' : ''
</script>

<style scoped>
/* scrolling inside modal */
.leaderboard-scroll { max-height: 70vh; overflow-y: auto; font-size: 1rem; line-height: 1.6; }

.headline-text { color: #333; font-weight: 700; margin: 10px 0 12px; }
.separator { border: none; border-top: 1px solid #e9ecef; margin: 18px 0 16px; }

/* identical look for both tables */
.leaderboard-table { table-layout: fixed; margin-bottom: 0; }
.leaderboard-table thead th { font-weight: 600; color: #333; background: #f8f9fa; }
.leaderboard-table .sticky { position: sticky; top: 0; z-index: 1; }
.leaderboard-table td, .leaderboard-table th { padding: .75rem .75rem; }

.method-cell strong { display: block; color: #111; }
.paper-link { display: inline-block; margin-top: 2px; text-decoration: none; color: #1a73e8; }
.paper-link:hover { text-decoration: underline; }

/* numbers are right-aligned and tabular for neat columns */
.num { text-align: right; font-variant-numeric: tabular-nums; }

/* highlight first row in both tables */
.top-row { background: #d8ecfb; }

/* bold per-column maxima */
.cell-strong { font-weight: 700; }

.table td { vertical-align: middle; }
</style>
