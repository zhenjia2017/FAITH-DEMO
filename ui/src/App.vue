<template>
  <div class="academic-header">
    <h1 class="main-title">
      <router-link
        :to="{ name: 'Guide' }"
        class="title-abbr"
        style="text-decoration: none; color: inherit;"
      >
        FAITH Demo
      </router-link>
    </h1>
    <h3>
      <span class="title-full">Faithful Temporal Question Answering over Heterogeneous Sources</span>
    </h3>
    <div class="subtitle-wrapper">
      <div class="academic-meta">
        <span class="meta-divider">·</span>
        <span class="meta-item" @click="handleIntroductionClick">
          <i class="bi bi-journal-bookmark"></i>
          Introduction
        </span>
        <span class="meta-divider">·</span>
        <span class="meta-item" @click="handleBenchmarksClick">
          <i class="bi bi-download"></i>
          Benchmarks
        </span>
        <span class="meta-divider">·</span>
        <span class="meta-item" @click="handleLeaderboardClick">
          <i class="bi bi-trophy"></i>
          Leaderboard
        </span>
        <span class="meta-divider">·</span>
        <span class="meta-item" @click="handleContactClick">
          <i class="bi bi-envelope"></i>
          Contact
        </span>
      </div>
    </div>
  </div>
  <BContainer>
    <div id="app" class="mb-32">
      <div class="answer-component">
        <AnswerComponent @question-submitted="handleQuestionSubmitted" />
      </div>
    </div>
    
    <!-- Configuration Card -->
    <!-- <BCard class="mt-4 mb-4 no-hover">
      <Configuration 
        @example-selected="onExampleSelected" 
        @config-changed="handleConfigChanged" />
    </BCard> -->

    <BCard
      class="mt-4 no-hover"
      no-body
      header-class="p-0"
    >
      <template #header>
        <div class="question-header d-flex justify-content-between align-items-center">
          <p class="question-text mb-0">Question: {{ currentData.question }}</p>
        </div>
      </template>
    </BCard>
    <b-card class="AR-SE no-hover">
      <!-- Answer Ranking Card -->
      <BCard class="mt-4 no-hover AR-SE-card" no-body>
        <template #header>
          <div class="header-toggle" @click="toggle">
            <h5 class="mb-0 fw-bold">Ranked Answers</h5>
            <i :class="isOpen ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
          </div>
        </template>
        <transition name="slide-fade">
          <div v-show="isOpen">
            <BCardBody>
              <BRow class="g-3">
                <template v-if="currentData.rankedAnswers.length">
                  <BCol
                    v-for="(answer, index) in currentData.rankedAnswers.slice(0, 5)"
                    :key="index"
                    md="6"
                    lg="4"
                  >
                    <BCard class="h-100 border border-3 border-light answer-bg shadow-sm">
                      <BCardBody>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                          <BBadge secondary pill>TOP {{ index + 1 }}</BBadge>
                          <BBadge bg="light" text-variant="dark"
                            v-if="initialMode != 'seq2seq_ha'">
                            {{ Number(answer.score).toFixed(3) }}
                          </BBadge>
                        </div>
                        <h6 class="card-title text-truncate fw-bold" :title="answer.label">{{ answer.label }}</h6>
                        <BCardText class="small text-muted mb-0">
                          ID:
                          <span v-if="answer.id && answer.id.startsWith('Q')">
                            <a
                              :href="`https://www.wikidata.org/wiki/${answer.id}`"
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {{ answer.id }}
                            </a>
                          </span>
                          <span v-else>
                            {{ answer.id }}
                          </span>
                        </BCardText>
                      </BCardBody>
                    </BCard>
                  </BCol>
                </template>
                <BCol v-else cols="12">
                  <BAlert variant="info" class="mb-0">NO answer information</BAlert>
                </BCol>
              </BRow>
            </BCardBody>
          </div>
        </transition>
      </BCard>

      <!-- Supporting Evidences Card -->
      
      <BCard class="mt-4 no-hover AR-SE-card" no-body>
        <template #header>
          <div class="header-toggle" @click="toggleEvidences">
            <h5 class="mb-0 fw-bold">Supporting Evidences</h5>
            <i :class="isEvidencesOpen ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
          </div>
        </template>
        <transition name="slide-fade">
          <BCollapse v-model="isEvidencesOpen">
            <BCardBody :class="{ 'p-0': !isEvidencesOpen }">
              <BRow class="g-3">
                <template v-if="currentData.evidences.length">
                  <BCol
                    v-for="(evidence, index) in currentData.evidences.slice(0, 5)"
                    :key="index"
                    cols="12"
                  >
                    <BCard
                      v-if="selectedTypes.includes(evidence.source)"
                      class="h-100 border border-light shadow-sm"
                    >
                      <BCardBody>
                        <div class="d-flex justify-content-between align-items-start mb-2">
                          <div class="d-flex align-items-center">
                            <BBadge secondary pill class="me-2">
                              <a
                                :href="evidence.url"
                                target="_blank"
                                rel="noopener noreferrer"
                                class="evidence-link"
                              >
                                Evidence {{ index + 1 }}
                              </a>
                            </BBadge>
                          </div>
                          <div class="d-flex align-items-center">
                            <BBadge bg="light" text-variant="dark" class="me-2"
                              v-if="initialMode != 'seq2seq_ha'">
                              {{ Number(evidence.score).toFixed(3) }}
                            </BBadge>
                            <BBadge bg="light" text-variant="dark" :title="'Source'">
                              <i :class="['bi', getSourceIcon(evidence.source)]"></i>
                              {{ getSourceName(evidence.source) }}
                            </BBadge>
                          </div>
                        </div>
                        <BCardText class="mb-0 evidence-text fw-bold" v-html="evidence.text"></BCardText>
                      </BCardBody>
                    </BCard>
                  </BCol>
                </template>
                <BCol v-else cols="12">
                  <BAlert variant="info" class="mb-0">
                    No evidences information
                  </BAlert>
                </BCol>
              </BRow>
            </BCardBody>
          </BCollapse>
        </transition>
      </BCard>
    </b-card>

    <b-card class="QU-ER-HA no-hover">
      <!-- Question Understanding Card -->
      <QuestionCard 
        :question="currentData.question" 
        :temporal-info="currentData.temporalInfo" 
        :intermediate-question-text="intermediateQuestionText" 
        :intermediate-temporal-info="intermediateTemporalInfo"
        :iterative-graphs="intermediateIterativeGraphData"
        :current-intermediate-page="intermediatePage"
        @update:currentIntermediatePage="(val: number) => intermediatePage = val"
        :answers="intermediateRankedAnswers"
        :evidences="intermediateEvidences"
        :graph-data="currentData.graphData"
        :selectedTypes="selectedTypes"
        :intermediate-initial-evidences-length="intermediateInitialEvidencesLength"
        :intermediate-initial-evidences-source="intermediateInitialEvidencesSource"
        :intermediate-pruned-evidences-length="intermediatePrunedEvidencesLength"
        :intermediate-pruned-evidences-source="intermediatePrunedEvidencesSource"
        :intermediate-topk-evidences-length="intermediateTopkEvidencesLength"
        :intermediate-topk-evidences-source="intermediateTopkEvidencesSource"
        :has-dual="isDualIntermediate"
        :dual-items="dualIntermediates"
      />
      <BCard class="mt-4 no-hover" no-body>
        <template #header>
          <div class="header-toggle">
            <h5 class="mb-0 fw-bold">Evidences Retrieval</h5>
          </div>
        </template>
        <BCardBody>
          <div class="stats-wrapper">
            <!-- Initial -->
            <div class="stat-item">
              <strong>Heterogeneous Retrieval ({{ currentData.initialEvidencesLength }})</strong>
              <div ref="initialPie" class="pie-chart"></div>
            </div>
            <div class="stat-arrow">
              <i class="bi bi-arrow-right-circle-fill"></i>
            </div>
            <!-- After pruning -->
            <div class="stat-item">
              <strong>Temporal Pruning ({{ currentData.prunedEvidencesLength }})</strong>
              <div ref="prunedPie" class="pie-chart"></div>
            </div>
            <div class="stat-arrow">
              <i class="bi bi-arrow-right-circle-fill"></i>
            </div>
            <!-- Top-K -->
            <div class="stat-item">
              <strong>Evidence Scoring ({{ currentData.topkEvidencesLength }})</strong>
              <div ref="topkPie" class="pie-chart"></div>
            </div>
          </div>
        </BCardBody>
      </BCard>


        <!-- Knowledge Graph Card -->
      <div
        v-if="initialMode === 'explaignn' || initialMode === 'graph_rag'"
        class="mt-4 text-center"
      >
        <!-- Assign a fixed id to the heading as the popover target -->
        <h3 id="graphsHeading" class="fw-bold text-center h3-with-dash">
          <span>Below are <span class="tp-emph">{{ totalPages }}</span> heterogeneous graphs:</span>
        </h3>

        <!-- Bind BPopover to the heading above -->
        <BPopover
          target="graphsHeading"
          placement="bottom"
          triggers="hover"
          html
          custom-class="popover-wide"
        >
          <div style="max-width: 800px;">
            <p style="margin:0;">
              1: Graphs in each <strong>pruning</strong> iteration, starting from the graph with initial top-100 evidence, to smaller ones.
            </p>
            <p style="margin:6px 0 0;">
              When <strong>the number of pruning iterations is 0</strong>, the graph with the initial top-100 evidence is in the answer prediction.
            </p>
            <p style="margin:6px 0 0;">
              2: Graph with answers and their supporting top-5 evidence in the answer prediction.
            </p>
          </div>
        </BPopover>

        <!-- Show pagination buttons only in GNN mode -->
        <div class="btn-group mt-2" v-if="initialMode === 'explaignn'">
          <button
            class="btn btn-secondary"
            :disabled="currentPage <= 1"
            @click="currentPage--"
          >
            <div class="fw-bold">&larr; Prev</div>
          </button>
          <button
            class="btn btn-secondary"
            :disabled="currentPage >= totalPages"
            @click="currentPage++"
          >
            <div class="fw-bold">Next &rarr;</div>
          </button>
        </div>

        <!-- Switch data source by mode: GNN uses iterativeGraphData, GraphRag uses candidateGraphData -->
        <GraphCard
          v-model:isCollapsed="isGraphCollapsed"
          :key="initialMode + '-' + currentPage"
          :graph-data="initialMode === 'explaignn'
            ? iterativeGraphData[currentPage - 1]
            : currentData.candidateGraphData"
          :ranked-answers="currentData.rankedAnswers"
          :highlight="initialMode === 'explaignn'
            ? (currentPage < totalPages
                ? { kind: 'candidate_text', texts: top5CandidateTexts }  /* Pages 1-2: highlight evidence texts */
                : { kind: 'answers', ids: top5AnswerIds })               /* Others: highlight answers */
            : { kind: 'candidate_text', texts: top5CandidateTexts }"
          :is-final="initialMode === 'explaignn'
            ? currentPage === totalPages
            : true"
        />
      </div>
      <!-- Candidate Evidences Card -->
      <BCard class="mt-4 no-hover" no-body v-if="initialMode === 'text_rag' || initialMode === 'seq2seq_ha'">
        <template #header>
          <div class="header-toggle" @click="toggleCandidate">
            <h5 class="mb-0 fw-bold">Candidate Evidences</h5>
            <i :class="isCandidateOpen ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
          </div>
        </template>

        <transition name="slide-fade">
          <BCollapse v-model="isCandidateOpen">
            <!-- Add candidate-evidence-body so the content can scroll -->
            <BCardBody class="candidate-evidence-body" :class="{ 'p-0': !isCandidateOpen }">
              <BRow class="g-3">
                <template v-if="currentData.evidences.length">
                  <BCol
                    v-for="(evidence, index) in currentData.evidences"
                    :key="index"
                    cols="12"
                  >
                    <BCard
                      v-if="selectedTypes.includes(evidence.source)"
                      class="h-80 border border-2 border-dark shadow-sm candidate-bg"
                    >
                      <BCardBody>
                        <div class="d-flex justify-content-between align-items-start mb-2">
                          <BBadge secondary pill class="me-2">
                            Evidence {{ index + 1 }}
                          </BBadge>
                          <div class="d-flex align-items-center">
                            <!-- <BBadge bg="light" text-variant="dark" class="me-2">
                              {{ (evidence.score * 100).toFixed(2) }}%
                            </BBadge> -->
                            <BBadge bg="light" text-variant="dark">
                              <i :class="['bi', getSourceIcon(evidence.source)]"></i>
                              {{ getSourceName(evidence.source) }}
                            </BBadge>
                          </div>
                        </div>
                        <BCardText class="mb-0 evidence-text fw-bold" v-html="evidence.text" />
                      </BCardBody>
                    </BCard>
                  </BCol>
                </template>
                <BCol v-else cols="12">
                  <BAlert variant="info" class="mb-0">
                    No candidate evidences available.
                  </BAlert>
                </BCol>
              </BRow>
            </BCardBody>
          </BCollapse>
        </transition>
      </BCard>
    </b-card>


    <!-- Include modal components -->
    <IntroductionModal
      v-model="showIntroductionModal"
      @close="handleModalClose('introduction')"
    />

    <BenchmarksModal
      v-model="showBenchmarksModal"
      @close="handleModalClose('benchmarks')"
    />

    <LeaderboardModal
      v-model="showLeaderboardModal"
      @close="handleModalClose('leaderboard')"
    />

    <ContactModal
      v-model="showContactModal"
      @close="handleModalClose('contact')"
    />
  </BContainer>
  <!-- Back to top -->
  <button
    type="button"
    class="back-to-top"
    :class="{ visible: showBackToTop }"
    @click="scrollToTop"
    aria-label="Back to top"
  >
    <i class="bi bi-arrow-up"></i>
  </button>

  <footer class="site-footer">
    <div class="footer-inner">
      <span>FAITH · Temporal QA System</span>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed, watch } from 'vue'
import * as echarts from 'echarts'
import { useRoute, useRouter } from 'vue-router'
import Configuration from './components/Configuration.vue';
import QuestionCard from './components/QuestionCard.vue'
import GraphCard from './components/Graphcard.vue'
import IntroductionModal from './components/IntroductionModal.vue'
import BenchmarksModal from './components/BenchmarksModal.vue'
import LeaderboardModal from './components/LeaderboardModal.vue'
import ContactModal from './components/ContactModal.vue'
import type { CurrentData, TemporalInfo, Evidence } from '@/types'
import {
  BContainer,
  BInputGroup,
  BButton,
  BBadge,
  BCard,
  BCardBody,
  BCardText,
  BRow,
  BCol,
  BAlert
} from 'bootstrap-vue-3'
import AnswerComponent from './components/AnswerComponent.vue'
import { RouterLink } from 'vue-router'
import { useConfigStore } from './stores/config'
const isDualIntermediate = ref(false)

type RankedAnswerLite = {
  id: string
  label: string
  score: number
  isCorrect: boolean
}

type IntermediateUnit = {
  question: string
  generated_q: string
  temporalInfo: TemporalInfo
  rankedAnswers: RankedAnswerLite[]
  evidences: Evidence[]
  initialEvidencesLength: number
  initialEvidencesSource: Record<string, number>
  prunedEvidencesLength: number
  prunedEvidencesSource: Record<string, number>
  topkEvidencesLength: number
  topkEvidencesSource: Record<string, number>
}

const dualIntermediates = ref<IntermediateUnit[]>([])

const isCandidateOpen = ref(true)
const toggleCandidate = () => {
  isCandidateOpen.value = !isCandidateOpen.value
}
const iterativeGraphData = ref<Array<{ nodes: any[]; links: any[]; question: string }>>([])
const currentPage          = ref(1)
const totalPages           = computed(() => iterativeGraphData.value.length)
const question = ref('');
const handleQuestionSubmitted = (submittedQuestion: string) => {
  question.value = submittedQuestion;
};
const rawCandidateEvidences = ref<any[]>([])

const isOpen = ref(false)
const toggle = () => {
  isOpen.value = !isOpen.value
}
const isEvidencesOpen = ref(false)
const toggleEvidences = () => {
  isEvidencesOpen.value = !isEvidencesOpen.value
}
const route = useRoute();
const router = useRouter();
const status = ref('Ready')
const isGraphCollapsed = ref(false)
const currentData = reactive<CurrentData>({
  question: '',
  temporalInfo: {},
  rankedAnswers: [],
  evidences: [],
  graphData: null,
  initialEvidencesLength: 0,
  initialEvidencesSource: { kb: 0, text: 0, info: 0, table: 0 },
  prunedEvidencesLength: 0,
  prunedEvidencesSource: { kb: 0, text: 0, info: 0, table: 0 },
  topkEvidencesLength: 0,
  topkEvidencesSource: { kb: 0, text: 0, info: 0, table: 0 },
  candidateGraphData: null
})
const selectedTypes = ref(["text", "kb", "table", "info"]);
const intermediateQuestionText = ref('');
const intermediateTemporalInfo = ref<TemporalInfo>({});
const intermediateGraphData = ref<any>(null);
const intermediateRankedAnswers = ref<Array<{ id: string; label: string; score: number; isCorrect: boolean }>>([]);
const intermediateEvidences = ref<Evidence[]>([])
const intermediateInitialEvidencesLength = ref(0)
const intermediateInitialEvidencesSource = ref<Record<string,number>>({})
const intermediatePrunedEvidencesLength = ref(0)
const intermediatePrunedEvidencesSource = ref<Record<string,number>>({})
const intermediateTopkEvidencesLength = ref(0)
const intermediateTopkEvidencesSource = ref<Record<string,number>>({})

// Control modal visibility flags
const showIntroductionModal = ref(false);
const showBenchmarksModal = ref(false);
const showLeaderboardModal = ref(false);
const showContactModal = ref(false);

// Handle modal open actions
const handleIntroductionClick = () => {
  showIntroductionModal.value = true;
};

const handleBenchmarksClick = () => {
  showBenchmarksModal.value = true;
};

const handleLeaderboardClick = () => {
  showLeaderboardModal.value = true;
};

const handleContactClick = () => {
  showContactModal.value = true;
};

// Handle modal close actions
const handleModalClose = (modalName: string) => {
  switch (modalName) {
    case 'introduction':
      showIntroductionModal.value = false;
      break;
    case 'benchmarks':
      showBenchmarksModal.value = false;
      break;
    case 'leaderboard':
      showLeaderboardModal.value = false;
      break;
    case 'contact':
      showContactModal.value = false;
      break;
  }
};
// Read question and config data from URL params
onMounted(() => {
  try {
    const raw = sessionStorage.getItem('qa_result');
    if (raw) {
      const result = JSON.parse(raw);
      processJsonData(result);
    } else {
      status.value = 'No result in session';
    }
  } catch (e) {
    console.error(e);
    status.value = 'Session parse error';
  }
  // Clean up query string in the address bar
  const webQuestion = currentData.question.replace(/ /g, '_')
  router.push({ query: { Currentquestion: webQuestion } });
});

const initialMode = ref<string>('');
onMounted(() => {
  const route = useRoute()
  const configStore = useConfigStore()

  initialMode.value = configStore.selectedRadioType2;
  const { sources, scorer, answerer, benchmark } = route.query
  if (sources) configStore.selectedCheckboxTypes = (sources as string).split(',')
  if (scorer) configStore.selectedRadioType1 = scorer as string
  if (answerer) configStore.selectedRadioType2 = answerer as string
  if (benchmark) configStore.selectedRadioType3 = benchmark as string
})
const configStore = useConfigStore()
// Restore configuration from query params
if (route.query.sources) {
  configStore.selectedCheckboxTypes = (route.query.sources as string).split(',')
}
if (route.query.scorer) {
  configStore.selectedRadioType1 = route.query.scorer as string
}
if (route.query.answerer) {
  configStore.selectedRadioType2 = route.query.answerer as string
}
if (route.query.benchmark) {
  configStore.selectedRadioType3 = route.query.benchmark as string
}

// Refs for attaching ECharts instances
const initialPie = ref<HTMLElement|null>(null)
const prunedPie  = ref<HTMLElement|null>(null)
const topkPie    = ref<HTMLElement|null>(null)

let initialChart: echarts.ECharts
let prunedChart: echarts.ECharts
let topkChart:   echarts.ECharts

// Draw pie charts with DOM nodes and data
function renderPie(
  el: HTMLElement,
  dataObj: Record<string, number>,
  title: string
) {
  const chart = echarts.init(el)

  const data = [
    { name: 'KB',    value: dataObj.kb    || 0 },
    { name: 'Text',  value: dataObj.text  || 0 },
    { name: 'Info',  value: dataObj.info  || 0 },
    { name: 'Table', value: dataObj.table || 0 },
  ]

  chart.setOption({
    color: ['#5470C6', '#91CC75', '#9A60B4', '#FAC858'],
    title: {
      text: title,
      left: 20,
      top: 4,
      textStyle: { fontSize: 12 }
    },
    tooltip: { trigger: 'item' },
    legend: {
      show: true,
      orient: 'vertical',
      right: 0,
      top: 'bottom',
      itemWidth: 12,
      itemHeight: 10,
      textStyle: { fontSize: 10 },
      data: data.map(d => d.name)
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['47%', '50%'],
      avoidLabelOverlap: false,
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: '12', fontWeight: 'bold' }
      },
      data
    }]
  })

  // Automatically respond to resize events
  const resizeHandler = () => {
    chart.resize()
  }
  window.addEventListener('resize', resizeHandler)

  // Override dispose to ensure listeners are removed on teardown
  const originalDispose = chart.dispose.bind(chart)
  chart.dispose = () => {
    window.removeEventListener('resize', resizeHandler)
    originalDispose()
  }

  return chart
}

onMounted(() => {
  // Watch source data and render immediately
  watch(() => currentData.initialEvidencesSource, src => {
    if (initialPie.value) {
      initialChart = renderPie(initialPie.value, src, '')
    }
  }, { immediate: true })

  watch(() => currentData.prunedEvidencesSource, src => {
    if (prunedPie.value) {
      prunedChart = renderPie(prunedPie.value, src, '')
    }
  }, { immediate: true })

  watch(() => currentData.topkEvidencesSource, src => {
    if (topkPie.value) {
      topkChart = renderPie(topkPie.value, src, '')
    }
  }, { immediate: true })
})

function toOrdinal(n: number): string {
  const s = ["th","st","nd","rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

// App.vue helpers
function onExampleSelected(q: string) {
  // Navigate to GuideView first without extra params
  router.push({
    name: 'Guide',
    query: { APPquestion: q }
  })
}

const configData = ref({
  selectedCheckboxTypes: ['text', 'kb', 'table', 'info'],
  selectedRadioType1: 'classifier',
  selectedRadioType2: 'explaignn',
  selectedRadioType3: 'timequestions'
});

// Handle configuration changes
const handleConfigChanged = (newConfig: any) => {
  configData.value = newConfig;
};

function extractTerms(tempinfo: any[]): string[] {
  if (!Array.isArray(tempinfo)) return []
  // Find the first list where every element is a string
  const found = tempinfo.find(
    (lst: any) => Array.isArray(lst) && lst.every(item => typeof item === 'string')
  )
  return Array.isArray(found) ? found as string[] : []
}


/**
 * Highlight every exact match of each term in text with a <span>
 */
function highlightTerms(text: string, terms: string[]): string {
  let result = text;
  // Sort by length desc to avoid short terms cutting long ones
  terms = terms.filter(t => !!t).sort((a, b) => b.length - a.length);
  for (const term of terms) {
    // Escape regex metacharacters
    const esc = term.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
    // Negative word boundary: ensure no word chars around term
    const regex = new RegExp(`(?<!\\w)${esc}(?!\\w)`, 'g');
    result = result.replace(regex, `<span style="color:#4d7922">${term}</span>`);
  }
  return result;
}

function annotateText(text: string, disambigs: [string, string][]): string {
  // Sort entities by label length desc to avoid splitting longer names
  const items = [...disambigs].sort((a, b) => b[0].length - a[0].length);
  let result = text;
  for (const [label, id] of items) {
    if (!label) continue;
    if (typeof id !== 'string' || !id.startsWith('Q')) continue;
    // 1) Escape regex special chars
    const esc = label.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&');
    // 2) Use negative word boundaries for full-phrase matches
    const regex = new RegExp(`(?<!\\w)${esc}(?!\\w)`, 'g');
    const url = `https://www.wikidata.org/wiki/${id}`;
    // 3) Use callback to wrap only the matched phrase
    result = result.replace(regex, match =>
      `<a href="${url}" target="_blank">${match}</a>`
    );
  }
  return result;
}

const intermediateIterativeGraphData = ref<Array<{ nodes:any[]; links:any[]; question:string }>>([])
const intermediatePage          = ref(1)
const totalIntermediatePages    = computed(() => intermediateIterativeGraphData.value.length)

const processJsonData = (data: any) => {
  const processedData = Array.isArray(data) ? data[0] : data;

  // Update question and time information
  currentData.question = processedData.question || processedData.Question || '';
  
  // Process structured time information
  if (processedData.structured_temporal_form || processedData.temporalInfo) {
    const tempInfo = processedData.temporalInfo || processedData.structured_temporal_form || {};
    currentData.temporalInfo = {
      entity: tempInfo.entity || '',
      category: tempInfo.category || '',
      relation: tempInfo.relation || '',
      answerType: tempInfo.answerType || tempInfo.answer_type || '',
      temporalSignal: tempInfo.temporalSignal || tempInfo.temporal_signal || '',
      temporalValues: tempInfo.temporalValues || tempInfo.temporal_value || []
    };
  } else {
    currentData.temporalInfo = {};
  }

  // Update answers
  if (processedData.answers) {
    currentData.rankedAnswers = processedData.answers.map((answer: any) => ({
      id: answer.id || '',
      label: answer.label || '',
      score: answer.score || 1.0,
      isCorrect: answer.isCorrect || false
    }));
  } else {
    currentData.rankedAnswers = [];
  }

  // Update evidences
  if (processedData.candidateEvidences) {
  // 1) Save the raw JSON first
    rawCandidateEvidences.value = processedData.candidateEvidences

    currentData.evidences = processedData.candidateEvidences.map((evidence: any) => {
      const raw = evidence.evidence_text || ''
      const withLinks = annotateText(raw, evidence.disambiguations || [])
      const terms = extractTerms(evidence.tempinfo || [])
      const finalHtml = highlightTerms(withLinks, terms)

      // Default to no link
      let url = ''
      if (Array.isArray(evidence.retrieved_for_entity) && evidence.retrieved_for_entity.length > 0) {
        const ent = evidence.retrieved_for_entity[0]

        if (evidence.source === 'kb' && ent.id) {
          if (ent.id.startsWith('P')) {
            // Property
            url = `https://www.wikidata.org/wiki/Property:${ent.id}`
          } else {
            // Item
            url = `https://www.wikidata.org/wiki/${ent.id}`
          }
        } else if (ent.wikipedia_path) {
          url = `https://en.wikipedia.org/wiki/${ent.wikipedia_path}`
        }
      }

      return {
        text: finalHtml,
        source: evidence.source || 'text',
        score: evidence.score || 1.0,
        isAnswering: evidence.is_answering_evidence || false,
        url
      }
    })

    currentData.initialEvidencesLength = processedData.initial_evidences_length ?? 0
    currentData.initialEvidencesSource = processedData.initial_evidences_source ?? {}
    currentData.prunedEvidencesLength  = processedData.pruned_evidences_length  ?? 0
    currentData.prunedEvidencesSource  = processedData.pruned_evidences_source  ?? {}
    currentData.topkEvidencesLength    = processedData.topk_evidences_length    ?? 0
    currentData.topkEvidencesSource    = processedData.topk_evidences_source    ?? {}
  } else {
    currentData.evidences = []
  }


  // Update intermediate question
  if (processedData.intermediateQuestions && processedData.intermediateQuestions.length > 0) {
    const list = processedData.intermediateQuestions as any[]

    // Normalize a single intermediateQuestion into an IntermediateUnit
    const normalizeIntermediateUnit = (item: any): IntermediateUnit => {
      const qStr  = item.question || ''
      const gqStr = item.generated_q || ''

      // temporal info
      let tinfo: TemporalInfo = {}
      if (item.temporalInfo || item.structured_temporal_form) {
        const tempInfo = item.temporalInfo || item.structured_temporal_form || {}
        tinfo = {
          entity:         tempInfo.entity || '',
          category:       tempInfo.category || '',
          relation:       tempInfo.relation || '',
          answerType:     tempInfo.answerType || tempInfo.answer_type || '',
          temporalSignal: tempInfo.temporalSignal || tempInfo.temporal_signal || '',
          temporalValues: tempInfo.temporalValues || tempInfo.temporal_value || []
        }
      }

      // ranked answers
      const rans: RankedAnswerLite[] = Array.isArray(item.ranked_answers)
        ? item.ranked_answers.map((it: any) => {
            const ans = it.answer || {}
            return {
              id:        ans.id || '',
              label:     ans.label || '',
              score:     it.score || 0,
              isCorrect: !!ans.is_answer
            }
          })
        : []

      // Evidences with entity links and highlighted temporal phrases
      const evs: Evidence[] = Array.isArray(item.candidate_evidences)
        ? item.candidate_evidences.map((evi: any) => {
            const raw   = evi.evidence_text || ''
            const linked = annotateText(raw, evi.disambiguations || [])
            const terms  = extractTerms(evi.tempinfo || [])
            const html   = highlightTerms(linked, terms)

            let url = ''
            if (Array.isArray(evi.retrieved_for_entity) && evi.retrieved_for_entity.length > 0) {
              const ent = evi.retrieved_for_entity[0]
              if (evi.source === 'kb' && ent.id) {
                url = ent.id.startsWith('P')
                  ? `https://www.wikidata.org/wiki/Property:${ent.id}`
                  : `https://www.wikidata.org/wiki/${ent.id}`
              } else if (ent.wikipedia_path) {
                url = `https://en.wikipedia.org/wiki/${ent.wikipedia_path}`
              }
            }

            return {
              text: html,
              source: evi.source || 'text',
              score: evi.score || 1.0,
              isAnswering: evi.is_answering_evidence || false,
              url
            }
          })
        : []

      return {
        question: qStr,
        generated_q: gqStr,
        temporalInfo: tinfo,
        rankedAnswers: rans,
        evidences: evs,
        initialEvidencesLength: item.initial_evidences_length ?? 0,
        initialEvidencesSource: item.initial_evidences_source ?? {},
        prunedEvidencesLength: item.pruned_evidences_length ?? 0,
        prunedEvidencesSource: item.pruned_evidences_source ?? {},
        topkEvidencesLength: item.topk_evidences_length ?? 0,
        topkEvidencesSource: item.topk_evidences_source ?? {}
      }
    }

    if (list.length === 1) {
      // Single-unit mode: keep original logic, prefer generated_q for display
      const iq = list[0]
      const unit = normalizeIntermediateUnit(iq)

      // Display text: prefer generated_q
      intermediateQuestionText.value = unit.generated_q || unit.question || ''

      // Keep original fields for single-card rendering
      intermediateTemporalInfo.value = unit.temporalInfo
      intermediateRankedAnswers.value = unit.rankedAnswers as any
      intermediateEvidences.value = unit.evidences
      intermediateInitialEvidencesLength.value = unit.initialEvidencesLength
      intermediateInitialEvidencesSource.value = unit.initialEvidencesSource
      intermediatePrunedEvidencesLength.value = unit.prunedEvidencesLength
      intermediatePrunedEvidencesSource.value = unit.prunedEvidencesSource
      intermediateTopkEvidencesLength.value = unit.topkEvidencesLength
      intermediateTopkEvidencesSource.value = unit.topkEvidencesSource

      // Prepare recursion with a single unit
      dualIntermediates.value = [unit]
      isDualIntermediate.value = false

    } else {
      // Dual-unit mode (take the first two)
      const unit1 = normalizeIntermediateUnit(list[0])
      const unit2 = normalizeIntermediateUnit(list[1])
      dualIntermediates.value = [unit1, unit2]
      isDualIntermediate.value = true

      // Display text: prefer generated_q (reuse old prop for template compatibility)
      intermediateQuestionText.value = unit1.generated_q || unit1.question || ''

      // Fill props with the first unit to stay compatible with the current QuestionCard
      intermediateTemporalInfo.value = unit1.temporalInfo
      intermediateRankedAnswers.value = unit1.rankedAnswers as any
      intermediateEvidences.value = unit1.evidences
      intermediateInitialEvidencesLength.value = unit1.initialEvidencesLength
      intermediateInitialEvidencesSource.value = unit1.initialEvidencesSource
      intermediatePrunedEvidencesLength.value = unit1.prunedEvidencesLength
      intermediatePrunedEvidencesSource.value = unit1.prunedEvidencesSource
      intermediateTopkEvidencesLength.value = unit1.topkEvidencesLength
      intermediateTopkEvidencesSource.value = unit1.topkEvidencesSource
    }
  } else {
    // No intermediateQuestions present
    intermediateQuestionText.value = ''
    intermediateTemporalInfo.value = {}
    intermediateRankedAnswers.value = []
    intermediateEvidences.value = []
    dualIntermediates.value = []
    isDualIntermediate.value = false
  }


  if (processedData.candidateEvidencesGexf) {
    const parser = new DOMParser();
    // If it is an array of strings, take the first; otherwise use directly
    const gexfStr = Array.isArray(processedData.candidateEvidencesGexf)
      ? processedData.candidateEvidencesGexf[0]
      : processedData.candidateEvidencesGexf;

    const xmlDoc = parser.parseFromString(gexfStr, 'text/xml');

    // Collect all <attribute> tags into a Map: id -> title
    const attrMap = new Map<string, string>();
    Array.from(xmlDoc.getElementsByTagName('attribute')).forEach(attr => {
      const id = attr.getAttribute('id');
      const title = attr.getAttribute('title');
      if (id && title) attrMap.set(id, title);
    });

    // Parse nodes
    const nodes = Array.from(xmlDoc.getElementsByTagName('node')).map(n => {
      const attrs: Record<string,string> = {};
      Array.from(n.getElementsByTagName('attvalue')).forEach(av => {
        const forId = av.getAttribute('for');
        const val   = av.getAttribute('value');
        if (forId && val) {
          const name = attrMap.get(forId) || forId;
          attrs[name] = val;
        }
      });
      return {
        id:   n.getAttribute('id'),
        name: n.getAttribute('label'),
        attributes: attrs
      };
    });

    // Parse edges
    const links = Array.from(xmlDoc.getElementsByTagName('edge')).map(e => ({
      source: e.getAttribute('source'),
      target: e.getAttribute('target'),
      value:  parseFloat(e.getAttribute('weight') || '1'),
      label:  e.getAttribute('label')
    }));

    // Attach parsed result to currentData, e.g., candidateGraphData
    currentData.candidateGraphData = {
      nodes,
      links,
      question: currentData.question
    };
    status.value = 'Candidate evidences graph parsed';
  } else {
    console.log("No candidateEvidencesGexf available");
  }
  fillIntermediateIterativeGraphs(processedData)
  fillIterativeGraphs(processedData)
}

// Evidence decomposition for intermediate questions
function fillIterativeGraphs(pd: any) {
  iterativeGraphData.value = []
  currentPage.value = 1

  if (!Array.isArray(pd.iterativeScoredEvidencesGexf)) return

  const parser = new DOMParser()

  pd.iterativeScoredEvidencesGexf.forEach((gexfStr: string) => {
    const xmlDoc = parser.parseFromString(gexfStr, 'text/xml')

    // Collect all <attribute> tags into a Map: id -> title
    const attrMap = new Map<string,string>()
    Array.from(xmlDoc.getElementsByTagName('attribute')).forEach(attr => {
      const id    = attr.getAttribute('id')
      const title = attr.getAttribute('title')
      if (id && title) attrMap.set(id, title)
    })

    const nodes = Array.from(xmlDoc.getElementsByTagName('node')).map(n => {
      const attributes: Record<string,string> = {}
      Array.from(n.getElementsByTagName('attvalue')).forEach(att => {
        const forId = att.getAttribute('for')
        const val   = att.getAttribute('value')
        if (forId && val) {
          // Use attrMap to map numeric id to real field name
          const name = attrMap.get(forId) || forId
          attributes[name] = val
        }
      })
      return {
        id:         n.getAttribute('id'),
        name:       n.getAttribute('label'),
        attributes
      }
    })

    const links = Array.from(xmlDoc.getElementsByTagName('edge')).map(e => ({
      source: e.getAttribute('source'),
      target: e.getAttribute('target'),
      value:  parseFloat(e.getAttribute('weight') || '1'),
      label:  e.getAttribute('label')
    }))

    iterativeGraphData.value.push({
      nodes,
      links,
      question: pd.question
    })
  })
}

// Evidence decomposition for the main question
function fillIntermediateIterativeGraphs(pd: any) {
  intermediateIterativeGraphData.value = []
  intermediatePage.value = 1

  if (!Array.isArray(pd.iterativeScoredIntermediateEvidencesGexf)) return

  const parser = new DOMParser()
  // Collect <attribute> id->title into a map
  pd.iterativeScoredIntermediateEvidencesGexf.forEach((gexfStr: string) => {
    const xmlDoc = parser.parseFromString(gexfStr, 'text/xml')
    const attrMap = new Map<string,string>()
    Array.from(xmlDoc.getElementsByTagName('attribute'))
         .forEach(a => { const id=a.getAttribute('id')!; const t=a.getAttribute('title')!; attrMap.set(id,t) })

    const nodes = Array.from(xmlDoc.getElementsByTagName('node')).map(n => {
      const attrs: Record<string,string> = {}
      Array.from(n.getElementsByTagName('attvalue')).forEach(av => {
        const key = av.getAttribute('for')!, v = av.getAttribute('value')!
        attrs[attrMap.get(key) || key] = v
      })
      return { id: n.getAttribute('id'), name: n.getAttribute('label'), attributes: attrs }
    })
    const links = Array.from(xmlDoc.getElementsByTagName('edge')).map(e => ({
      source: e.getAttribute('source'),
      target: e.getAttribute('target'),
      value:  parseFloat(e.getAttribute('weight')||'1'),
      label:  e.getAttribute('label')
    }))
    intermediateIterativeGraphData.value.push({ nodes, links, question: pd.question })
  })
}

const fetchGraphData = async (processedData: any) => {
  try {
    const response = await fetch('/api/convert', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify([processedData])
    });

    if (!response.ok) {
      throw new Error('API request error');
    }

    const result = await response.json();
    if (result.error) {
      throw new Error(result.error);
    }

    // Parse GEXF data
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(result.gexf, 'text/xml');
    
    // Extract nodes and edges
    const nodes = Array.from(xmlDoc.getElementsByTagName('node')).map(node => {
      const attributes: Record<string, string> = {};
      const attvalues = node.getElementsByTagName('attvalue');
      for (const attvalue of attvalues) {
        const attrId = attvalue.getAttribute('for');
        const value = attvalue.getAttribute('value');
        if (attrId !== null && value !== null) {
          const attrElem = xmlDoc.querySelector(`attribute[id="${attrId}"]`);
          if (attrElem) {
            const attrName = attrElem.getAttribute('title');
            if (attrName) {
              attributes[attrName] = value;
            }
          }
        }
      }
      
      return {
        id: node.getAttribute('id'),
        name: node.getAttribute('label'),
        attributes
      };
    });

    const links = Array.from(xmlDoc.getElementsByTagName('edge')).map(edge => ({
      source: edge.getAttribute('source'),
      target: edge.getAttribute('target'),
      value: parseFloat(edge.getAttribute('weight') || '1'),
      label: edge.getAttribute('label')
    }));

    // Update graph data
    currentData.graphData = {
      nodes,
      links,
      question: currentData.question
    };
    
    status.value = 'Analysis completed with graph conversion';
  } catch (error: any) {
    console.error('Graph API error:', error);
    status.value = `Graph conversion error: ${error instanceof Error ? error.message : 'Unknown error'}`;
  }
}

const getSourceIcon = (source?: string): string => {
  if (!source) return 'bi-question-circle';
  switch(source) {
    case 'kb': return 'bi-database-fill'
    case 'text': return 'bi-file-text-fill'
    case 'table': return 'bi-table'
    case 'web': return 'bi-globe'
    case 'info': return 'bi-info-square-fill'
    default: return 'bi-question-circle'
  }
}

const getSourceName = (source?: string): string => {
  if (!source) return 'Unknown source';
  const sourceNames: Record<string, string> = {
    'kb': 'KB',
    'text': 'Text',
    'table': 'Table',
    'web': 'Web',
    'NERD': 'NERD',
    'info': 'Info'
  }
  return sourceNames[source] || 'Unknown source'
}
// Normalize text: trim ends, collapse whitespace, unify newlines/spaces
const normalizeText = (s: string) =>
  (s ?? '')
    .replace(/\r\n/g, '\n')
    .replace(/\u00A0/g, ' ')           // nbsp -> space
    .replace(/\s+/g, ' ')              // collapse whitespaces
    .trim()

// Top-5 candidate evidences (sorted by score desc) using raw evidence_text
const top5CandidateTexts = computed(() => {
  // rawCandidateEvidences stores backend raw objects
  const src = Array.isArray(rawCandidateEvidences.value) ? rawCandidateEvidences.value : []
  return [...src]
    .sort((a, b) => (b?.score ?? 0) - (a?.score ?? 0))
    .slice(0, 5)
    .map(e => normalizeText(e?.evidence_text || ''))
    .filter(Boolean)
})

// Top-5 answers
const top5AnswerIds = computed(() => {
  return [...currentData.rankedAnswers]
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
    .slice(0, 5)
    .map(a => a.id)
    .filter(Boolean)
})
const showBackToTop = ref(false)

const handleScroll = () => {
  const y = window.pageYOffset || document.documentElement.scrollTop || 0
  showBackToTop.value = y > window.innerHeight
}

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  handleScroll()
})
onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style>
body {
  margin: 0 !important;
  padding: 0 !important;
  background-color: #e7e7e7 !important;
}
.AR-SE-card {
  background-color: #f3faf5 !important;
}
.mb-32 {
  margin-bottom: 32px !important;
}
.academic-header {
  background: linear-gradient(to bottom, #b0d48c, #f1f0f0);
  background-size: 170% 170%;
  padding: 30px;
  border-bottom: 1px solid #e9ecef;
  text-align: center;
  margin-bottom: 2rem;
}

.main-title {
  padding: 50px 0 20px 0;
  font-size: 5rem;
  color: #283c64;
  margin-bottom: 0;
}

.sub-title {
  margin-bottom: 15px;
}

.title-abbr {
  font-weight: bold;
  color: #283c64;
  font-size: 90px;
}

.title-full {
  color: #283c64;
  font-weight: bold;
  font-size: 35px;
}

.subtitle-wrapper {
  margin-top: 10px;
}

.academic-meta {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  padding-bottom: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  font-size: 1rem;
  color: #007bff;
  margin: 5px 10px;
  cursor: pointer;
  transition: color 0.3s ease;
  font-weight: bold;
}

.meta-item:hover {
  color: #0056b3;
}

.meta-item i {
  margin-right: 5px;
}
.h3-with-dash { display: block; }
.h3-with-dash > span {
  display: inline-block;
  border-bottom: 2px dashed rgba(50,50,50,.35);
  padding-bottom: 4px;
  line-height: 1.2;
}
.h3-with-dash::after {
  content: "";
  position: absolute;
  left: 0; right: 0; bottom: 0;
  border-bottom: 2px dashed rgba(50, 50, 50, .35);
}
.popover.popover-wide { 
  max-width: 820px !important;
}
.tp-emph {
  color: #283c64;
  font-weight: 800;
}

.meta-divider {
  color: #6c757d;
  margin: 0 10px;
}

@media (max-width: 768px) {
  .main-title {
    font-size: 2rem;
  }

  .title-full {
    display: block;
    font-size: 1.5rem;
  }

  .academic-meta {
    flex-direction: column;
  }

  .meta-item {
    margin: 5px 0;
  }

  .meta-divider {
    display: none;
  }
}

:root {
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --border-radius: 8px;
            --box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
            --transition-time: 0.3s;
        }

        body {
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f8f9fb;
            color: #2c3e50;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            padding: 30px;
        }


        .card {
            border: none;
            box-shadow: var(--box-shadow);
            transition: all var(--transition-time);
            margin-bottom: 1.5rem;
            border-radius: var(--border-radius);
            overflow: hidden;
        }

        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
        }
.candidate-evidence-container {
  max-height: 400px;
  overflow-y: auto;
}
.evidence-text {
  white-space: pre-wrap;
            font-size: 0.9rem;
  line-height: 1.5;
}
.popover-wide {
  max-width: 800px;
}
.card-body {
  transition: height 0.3s ease-in-out;
            overflow: hidden;
        }
        
        .collapse-btn {
  transition: all 0.3s ease;
}

.candidate-evidence-body {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 0.5rem; /* Prevent scrollbar from covering content */
}
/* Transition duration and easing */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}

/* Enter/leave start: hidden, height 0, slight upward shift, transparent */
.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-10px);
}

/* Enter/leave end: fully visible, tall enough, original position */
.slide-fade-enter-to,
.slide-fade-leave-from {
  opacity: 1;
  max-height: 2000px; /* Ensure large content can expand */
  transform: translateY(0);
}

.collapse-btn.collapsed {
            transform: rotate(180deg);
        }
      
.back-to-top {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 1050;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 9999px;
  display: grid;
  place-items: center;
  background: #283c64;
  color: #fff;
  box-shadow: 0 8px 20px rgba(0,0,0,.15);
  cursor: pointer;

  /* Entrance animation (hidden by default) */
  opacity: 0;
  transform: translateY(10px);
  pointer-events: none;
  transition: opacity .2s ease, transform .2s ease, box-shadow .2s ease, background .2s ease;
}
.back-to-top.visible {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}
.back-to-top:hover {
  box-shadow: 0 10px 24px rgba(0,0,0,.2);
  background: #1f2f50;
}
.back-to-top i {
  font-size: 20px;
  line-height: 1;
}

</style>

<style scoped>
.AR-SE {
  background-color: #b4d7b4 !important
}
.QU-ER-HA {
  background-color: #bbc8da !important
}
.stats-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: nowrap;
}

.stat-item {
  flex: 1 1 calc(33.333% - 16px);
  border: 1px solid #dee2e6;
  border-radius: .5rem;
  padding: 1rem .5rem 0.5rem;
  background: #fff;
  text-align: center;
  position: relative;
}

.pie-chart {
  width: 100%;
  height: 150px;
  margin-top: .5rem;
}

.stat-arrow {
  display: flex;
  align-items: center;
}

.stat-arrow i {
  font-size: 2rem;
  color: #6c757d;
}

.answer-bg {
  background-color: #b0d48c65;
  border-radius: 15px;
  font-weight: bold;
}
.candidate-bg {
  background-color: #e4e4e4;
}
.question-header {
  background: linear-gradient(90deg, #b0d48c1f, #ecf7ee);
  padding: 1rem 1rem;
  border-radius: 0.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.question-text {
  white-space: pre-wrap;
  margin: 0;
  color: #333;
  font-size: 1.5rem;
  font-weight: bold;
}
.no-hover {
  transition: none !important;
  box-shadow: none !important;
}
.no-hover:hover {
  box-shadow: none !important;
  transform: none !important;
}

:deep(.card-header) {
  padding: 20px 16px;
}
.header-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  width: 100%;
}
.site-footer {
  background: #424242;
  color: #fff;
  padding: 14px 0;
  margin-top: 24px;
}

.footer-inner {
  max-width: 1140px;  /* Close to BContainer width */
  margin: 0 auto;
  padding: 0 12px;
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.dot {
  opacity: .6;
}

.site-footer a {
  color: #fff;
  text-decoration: none;
  border-bottom: 1px dashed rgba(255,255,255,.4);
}

.site-footer a:hover {
  border-bottom-color: #fff;
}

.evidence-link {
  color: #fff;
  text-decoration: none;
}

.evidence-link:hover {
  color: #e0e0e0;
  text-decoration: none;
}

</style>