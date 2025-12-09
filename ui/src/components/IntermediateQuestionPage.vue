<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted, reactive } from 'vue'
import { useRoute } from 'vue-router'
import QuestionCard from './QuestionCard.vue'
import * as echarts from 'echarts'
import { type NodeStyle } from '@/types'

interface Answer {
  id: string
  label: string
  score: number
  isCorrect: boolean
}

interface RawEvidence {
  evidence_text: string
  source: string
  score: number
  isAnswering: boolean
}

interface Evidence {
  text: string
  source: string
  score: number
  isAnswering: boolean
}

interface TemporalInfo {
  entity: string
  category: string
  relation: string
  answerType: string
  temporalSignal: string
  temporalValues: any[][]
}

const route = useRoute();
const props = withDefaults(defineProps<{
  question?: string
}>(), {
  question: ''
});

const currentQuestion = ref(props.question || '');
watch(() => route.params.question, (newQuestion) => {
  if (typeof newQuestion === 'string') {
    currentQuestion.value = newQuestion;
  }
}, { immediate: true });

const answers = ref<Answer[]>([]);
const candidateEvidences = ref<RawEvidence[]>([]);
const graphData = ref<any>(null);
const chartContainer = ref<HTMLElement | null>(null);
let chart: echarts.ECharts | null = null;

const questionCardProps = reactive<{
  question: string
  temporalInfo: TemporalInfo
  intermediateQuestionText: string
  intermediateTemporalInfo: TemporalInfo
  intermediateGraphData?: any
  answers: Answer[]
  evidences: Evidence[]
  graphData?: any
  selectedTypes: string[]
}>({
  question: currentQuestion.value,
  temporalInfo: {
    entity: '',
    category: '',
    relation: '',
    answerType: '',
    temporalSignal: '',
    temporalValues: [[]]
  },
  intermediateQuestionText: '',
  intermediateTemporalInfo: {
    entity: '',
    category: '',
    relation: '',
    answerType: '',
    temporalSignal: '',
    temporalValues: [[]]
  },
  answers: [],
  evidences: [],
  graphData: null,
  selectedTypes: ['text', 'kb', 'table', 'infobox']
});

// Watch data changes to update props
watch(currentQuestion, (newQuestion) => {
  questionCardProps.question = newQuestion;
});

watch(answers, (newAnswers) => {
  questionCardProps.answers = newAnswers;
});

watch(candidateEvidences, (newEvidences: RawEvidence[]) => {
  questionCardProps.evidences = newEvidences.map(evidence => ({
    text: evidence.evidence_text,
    source: evidence.source,
    score: evidence.score,
    isAnswering: evidence.isAnswering
  }));
});

watch(graphData, (newGraphData) => {
  questionCardProps.graphData = newGraphData;
});

const getColor = (type: string) => {
  const colors = {
    'evidence_text': '#73C0DE',
    'wikidata_entity': '#91CC75',
    'retrieved_for_entity': '#FAC858',
    'disambiguation': '#EE6666',
    'tempinfo': '#5470C6',
    'other': '#3BA272'
  }
  return colors[type as keyof typeof colors] || colors.other
}

const getNodeSize = (node: any, totalNodes: number) => {
  const type = node.attributes?.type || 'other'
  const isAnswering = node.attributes?.is_answering === 'true'
  const isAnswer = node.attributes?.is_answer === 'true'
  const isLargeGraph = totalNodes > 100

  let size = isLargeGraph ? 15 : 30

  switch(type) {
    case 'evidence_text':
      size = isLargeGraph ? 20 : 50
      break
    case 'wikidata_entity':
      size = isLargeGraph ? 
            (isAnswer ? 25 : 18) : 
            (isAnswer ? 60 : 40)
      break
    case 'retrieved_for_entity':
      size = isLargeGraph ? 16 : 35
      break
    case 'disambiguation':
      size = isLargeGraph ? 16 : 35
      break
    case 'tempinfo':
      size = isLargeGraph ? 18 : 40
      break
  }

  return size
}

const getNodeSymbol = (type: string, source?: string) => {
  if (type === 'evidence_text') {
    switch(source) {
      case 'kb': 
        return 'path://M832 64H192c-17.7 0-32 14.3-32 32v832c0 17.7 14.3 32 32 32h640c17.7 0 32-14.3 32-32V96c0-17.7-14.3-32-32-32zM280 795.7c0 13.4-10.9 24.3-24.3 24.3h-30.4c-13.4 0-24.3-10.9-24.3-24.3v-30.4c0-13.4 10.9-24.3 24.3-24.3h30.4c13.4 0 24.3 10.9 24.3 24.3v30.4zm0-128c0 13.4-10.9 24.3-24.3 24.3h-30.4c-13.4 0-24.3-10.9-24.3-24.3v-30.4c0-13.4 10.9-24.3 24.3-24.3h30.4c13.4 0 24.3 10.9 24.3 24.3v30.4zm384 256c0 13.4-10.9 24.3-24.3 24.3H375.7c-13.4 0-24.3-10.9-24.3-24.3v-30.4c0-13.4 10.9-24.3 24.3-24.3h264c13.4 0 24.3 10.9 24.3 24.3v30.4zm0-128c0 13.4-10.9 24.3-24.3 24.3H375.7c-13.4 0-24.3-10.9-24.3-24.3v-30.4c0-13.4 10.9-24.3 24.3-24.3h264c13.4 0 24.3 10.9 24.3 24.3v30.4zm0-128c0 13.4-10.9 24.3-24.3 24.3H375.7c-13.4 0-24.3-10.9-24.3-24.3v-30.4c0-13.4 10.9-24.3 24.3-24.3h264c13.4 0 24.3 10.9 24.3 24.3v30.4z'
      case 'text': 
        return 'path://M854.6 288.6L639.4 73.4c-6-6-14.1-9.4-22.6-9.4H192c-17.7 0-32 14.3-32 32v832c0 17.7 14.3 32 32 32h640c17.7 0 32-14.3 32-32V311.3c0-8.5-3.4-16.7-9.4-22.7zM790.2 326H602V137.8L790.2 326zm1.8 562H232V136h302v216c0 23.2 18.8 42 42 42h216v494z'
      case 'table': 
        return 'path://M928 160H96c-17.7 0-32 14.3-32 32v640c0 17.7 14.3 32 32 32h832c17.7 0 32-14.3 32-32V192c0-17.7-14.3-32-32-32zm-40 208H136v-96h752v96zm0 176H136v-96h752v96zm0 176H136v-96h752v96z'
      case 'web': 
        return 'path://M925.6 405.1l-203-253.7c-1.2-1.5-3.1-2.4-5-2.4H306.4c-1.9 0-3.8 0.9-5 2.4l-203 253.7c-1.9 2.4-1.9 5.9 0 8.2l203 253.7c1.2 1.5 3.1 2.4 5 2.4h411.2c1.9 0 3.8-0.9 5-2.4l203-253.7C927.5 411 927.5 407.5 925.6 405.1zM814.4 394.8l-129 129-129-129h258zM307.6 394.8l129-129 129 129H307.6z'
      case 'infobox':
        return 'path://M880 112H144c-17.7 0-32 14.3-32 32v736c0 17.7 14.3 32 32 32h736c17.7 0 32-14.3 32-32V144c0-17.7-14.3-32-32-32zM648.3 310.1l43.7-43.7c4.7-4.7 12.3-4.7 17 0l83.9 83.9c4.7 4.7 4.7 12.3 0 17l-43.7 43.7c-4.7 4.7-12.3 4.7-17 0l-83.9-83.9c-4.7-4.7-4.7-12.3 0-17zM272.9 746.9c-6.6 0-10.4-7.7-6.3-12.9l143.7-171.7c4.7-5.6 12-6.3 17.6-2.3l98.8 70.9c5.7 4.1 14 3.4 18.8-1.5l43.2-44.1c6.9-7 18.2-7.3 25.4-0.6l33.4 31c9.3 8.7 23.8 8.1 32.4-1.2l65.2-70.9c6.1-6.6 16.4-6.7 22.6-0.2l135.2 140.7c6 6.2 1.5 16.5-7.2 16.5h-624.2z'
      default: 
        return 'circle'
    }
  }
  
  switch(type) {
    case 'wikidata_entity': 
      return 'diamond'
    case 'retrieved_for_entity': 
      return 'triangle'
    case 'disambiguation': 
      return 'rect'
    case 'tempinfo': 
      return 'pin'
    default: 
      return 'circle'
  }
}

const getNodeStyle = (node: any, totalNodes: number): NodeStyle => {
  const type = node.attributes?.type || 'other'
  const isAnswering = node.attributes?.is_answering === 'true'
  const isAnswer = node.attributes?.is_answer === 'true'
  const source = node.attributes?.source
  const isLargeGraph = totalNodes > 100

  let style: NodeStyle = {
    itemStyle: {
      color: getColor(type),
      borderWidth: isLargeGraph ? 1 : 2,
      borderType: 'solid',
      shadowColor: 'rgba(0, 0, 0, 0.2)',
      shadowBlur: isLargeGraph ? 2 : 5,
      opacity: isLargeGraph ? 0.7 : 0.9
    }
  }

  if (isAnswer) {
    style.itemStyle.borderColor = '#91CC75'
    style.itemStyle.borderWidth = isLargeGraph ? 2 : 4
    style.itemStyle.shadowBlur = isLargeGraph ? 10 : 20
    style.itemStyle.shadowColor = 'rgba(145, 204, 117, 0.5)'
    style.itemStyle.opacity = 1
  }

  if (type === 'tempinfo') {
    style.itemStyle.borderColor = '#5470C6'
    style.itemStyle.borderWidth = isLargeGraph ? 1.5 : 3
    style.itemStyle.shadowBlur = isLargeGraph ? 8 : 15
  }

  if (type === 'evidence_text') {
    style.itemStyle.opacity = isLargeGraph ? 0.6 : 0.85
    style.itemStyle.shadowBlur = isLargeGraph ? 5 : 10
  }

  return style
};

const initGraph = () => {
  if (!chartContainer.value || !graphData.value) return;
  
  if (!chart) {
    chart = echarts.init(chartContainer.value);
  }

  const evidenceTextCount = graphData.value.nodes.filter((node: any) => 
    node.attributes?.type === 'evidence_text'
  ).length;

  const nodes = graphData.value.nodes.map((node: any) => ({
    ...node,
    symbolSize: getNodeSize(node, graphData.value.nodes.length),
    symbol: getNodeSymbol(node.attributes?.type, node.attributes?.source),
    ...getNodeStyle(node, graphData.value.nodes.length),
    label: {
      show: node.attributes?.type === 'evidence_text' ? 
            (evidenceTextCount < 50) : true,
      position: 'right',
      formatter: node.name,
      fontSize: node.attributes?.is_answer === 'true' ? 14 : 12,
      color: '#2c3e50'
    }
  }));

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const { data } = params
        if (!data) return ''
        
        const attrs = data.attributes || {}
        const info = [
          `名称: ${data.name}`,
          `类型: ${attrs.type || 'Unknow'}`,
          `分数: ${(parseFloat(attrs.score || 0) * 100).toFixed(2)}%`,
          `是否为答案: ${attrs.is_answer === 'true' ? '是' : '否'}`
        ]
        return info.join('<br>')
      },
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#eee',
      borderWidth: 1,
      padding: [10, 15],
      textStyle: {
        color: '#2c3e50'
      }
    },
    legend: {
      data: [
        { name: '证据文本', icon: 'circle' },
        { name: '维基数据实体', icon: 'diamond' },
        { name: '时间信息', icon: 'pin' },
        { name: '知识库来源', icon: 'path://M832 64H192c-17.7 0-32 14.3-32 32v832c0 17.7 14.3 32 32 32h640c17.7 0 32-14.3 32-32V96c0-17.7-14.3-32-32-32zM280 795.7c0 13.4-10.9 24.3-24.3 24.3h-30.4c-13.4 0-24.3-10.9-24.3-24.3v-30.4c0-13.4 10.9-24.3 24.3-24.3h30.4c13.4 0 24.3 10.9 24.3 24.3v30.4zm0-128c0 13.4-10.9 24.3-24.3 24.3h-30.4c-13.4 0-24.3-10.9-24.3-24.3v-30.4c0-13.4 10.9-24.3 24.3-24.3h30.4c13.4 0 24.3 10.9 24.3 24.3v30.4zm384 256c0 13.4-10.9 24.3-24.3 24.3H375.7c-13.4 0-24.3-10.9-24.3-24.3v-30.4c0-13.4 10.9-24.3 24.3-24.3h264c13.4 0 24.3 10.9 24.3 24.3v30.4zm0-128c0 13.4-10.9 24.3-24.3 24.3H375.7c-13.4 0-24.3-10.9-24.3-24.3v-30.4c0-13.4 10.9-24.3 24.3-24.3h264c13.4 0 24.3 10.9 24.3 24.3v30.4zm0-128c0 13.4-10.9 24.3-24.3 24.3H375.7c-13.4 0-24.3-10.9-24.3-24.3v-30.4c0-13.4 10.9-24.3 24.3-24.3h264c13.4 0 24.3 10.9 24.3 24.3v30.4z' },
        { name: '文本来源', icon: 'path://M854.6 288.6L639.4 73.4c-6-6-14.1-9.4-22.6-9.4H192c-17.7 0-32 14.3-32 32v832c0 17.7 14.3 32 32 32h640c17.7 0 32-14.3 32-32V311.3c0-8.5-3.4-16.7-9.4-22.7zM790.2 326H602V137.8L790.2 326zm1.8 562H232V136h302v216c0 23.2 18.8 42 42 42h216v494z' },
        { name: '表格来源', icon: 'path://M928 160H96c-17.7 0-32 14.3-32 32v640c0 17.7 14.3 32 32 32h832c17.7 0 32-14.3 32-32V192c0-17.7-14.3-32-32-32zm-40 208H136v-96h752v96zm0 176H136v-96h752v96zm0 176H136v-96h752v96z' },
        { name: '网页来源', icon: 'path://M925.6 405.1l-203-253.7c-1.2-1.5-3.1-2.4-5-2.4H306.4c-1.9 0-3.8 0.9-5 2.4l-203 253.7c-1.9 2.4-1.9 5.9 0 8.2l203 253.7c1.2 1.5 3.1 2.4 5 2.4h411.2c1.9 0 3.8-0.9 5-2.4l203-253.7C927.5 411 927.5 407.5 925.6 405.1zM814.4 394.8l-129 129-129-129h258zM307.6 394.8l129-129 129 129H307.6z' }
      ],
      left: 30,
      top: 60,
      orient: 'vertical',
      textStyle: {
        color: '#2c3e50'
      },
      itemWidth: 16,
      itemHeight: 16,
      itemGap: 10,
      formatter: (name: string) => {
        const counts = {
          '证据文本': graphData.value.nodes.filter((n: any) => n.attributes?.type === 'evidence_text').length || 0,
          '维基数据实体': graphData.value.nodes.filter((n: any) => n.attributes?.type === 'wikidata_entity').length || 0,
          '时间信息': graphData.value.nodes.filter((n: any) => n.attributes?.type === 'tempinfo').length || 0,
          '知识库来源': graphData.value.nodes.filter((n: any) => n.attributes?.source === 'kb').length || 0,
          '文本来源': graphData.value.nodes.filter((n: any) => n.attributes?.source === 'text').length || 0,
          '表格来源': graphData.value.nodes.filter((n: any) => n.attributes?.source === 'table').length || 0,
          '网页来源': graphData.value.nodes.filter((n: any) => n.attributes?.source === 'web').length || 0
        }
        return `${name} (${counts[name as keyof typeof counts] || 0})`
      }
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      links: graphData.value.links.map((link: any) => ({
        ...link,
        lineStyle: {
          width: Math.max(1, Math.min(2.5, Math.pow(link.value || 1, 0.6) * 1.5)),
          color: link.value > 0.8 ? 'rgba(84, 112, 198, 0.9)' :
                link.value > 0.5 ? 'rgba(84, 112, 198, 0.7)' :
                link.value > 0.3 ? 'rgba(84, 112, 198, 0.5)' :
                'rgba(84, 112, 198, 0.3)',
          curveness: 0.1
        }
      })),
      categories: [
        { name: '证据文本' },
        { name: '维基数据实体' },
        { name: '时间信息' },
        { name: '知识库来源' },
        { name: '文本来源' },
        { name: '表格来源' },
        { name: '网页来源' }
      ],
      force: {
        repulsion: [50, 500],
        edgeLength: [50, 200],
        gravity: 0.1
      },
      emphasis: {
        focus: 'adjacency',
        scale: true,
        lineStyle: {
          width: 4
        },
        label: {
          show: true,
          fontSize: (params: any) => params.data.attributes?.is_answer === 'true' ? 16 : 14,
          backgroundColor: 'rgba(255,255,255,0.95)',
          padding: [4, 8],
          borderRadius: 4
        },
        itemStyle: {
          shadowBlur: (params: any) => params.data.attributes?.is_answer === 'true' ? 20 : 10,
          shadowColor: (params: any) => params.data.attributes?.is_answer === 'true' ? 
              'rgba(46, 204, 113, 0.4)' : 'rgba(0, 0, 0, 0.2)',
          borderWidth: (params: any) => params.data.attributes?.is_answer === 'true' ? 4 : 2
        }
      },
      nodeScaleRatio: 0.6
    }]
  };

  chart.setOption(option);
};

watch(() => graphData.value, (newVal) => {
  if (newVal) {
    initGraph();
  }
}, { deep: true });

onMounted(() => {
  fetchData();
  window.addEventListener('resize', () => chart?.resize());
});

onUnmounted(() => {
  chart?.dispose();
  window.removeEventListener('resize', () => chart?.resize());
});

async function fetchData() {
  if (currentQuestion.value) {
    try {
      const response = await fetch(`/api/intermediate-question?question=${encodeURIComponent(currentQuestion.value)}`);
      if (!response.ok) {
        throw new Error('请求失败');
      }
      const data = await response.json();
      
      if (data.answers) {
        answers.value = data.answers.map((answer: any) => ({
          ...answer,
          score: answer.score || 0,
          isCorrect: answer.isCorrect || false
        }));
      }
      if (data.candidateEvidences) {
        candidateEvidences.value = data.candidateEvidences.map((evidence: any) => ({
          ...evidence,
          text: evidence.evidence_text,
          score: evidence.score || 0,
          isAnswering: evidence.isAnswering || false,
          source: evidence.source || 'unknown'
        }));
      }
      if (data.graphData) {
        graphData.value = data.graphData;
      }
      if (data.temporalInfo) {
        questionCardProps.temporalInfo = data.temporalInfo;
      }
      if (data.intermediateQuestionText) {
        questionCardProps.intermediateQuestionText = data.intermediateQuestionText;
      } else if (data.intermediate_question_pipeline_result && data.intermediate_question_pipeline_result.length > 0) {
        questionCardProps.intermediateQuestionText = data.intermediate_question_pipeline_result[0].generated_q;
      }
    } catch (error: any) {
      console.error('Failed to retrieve data:', error);
    }
  }
}

function getSourceIcon(source: string | undefined) {
  const iconMap = {
    'wikipedia': 'bi bi-wikipedia',
    'web': 'bi bi-globe',
    'news': 'bi bi-newspaper',
    'book': 'bi bi-book',
    'document': 'bi bi-file-text',
    'infobox': 'bi bi-info-square-fill'
  };
  return iconMap[source?.toLowerCase() as keyof typeof iconMap] || 'bi bi-question-circle';
}

function getSourceName(source: string | undefined) {
  const nameMap = {
    'wikipedia': 'Wikipedia',
    'web': 'Web',
    'news': 'News',
    'book': 'Book',
    'document': 'Document',
    'infobox': 'Infobox'
  };
  return nameMap[source?.toLowerCase() as keyof typeof nameMap] || 'Unknow source';
}
</script>

<template>
  <div class="container mt-4">
    <h1>Intermediate question handling</h1>
    
    <!-- Question understanding -->
    <QuestionCard 
      :question="questionCardProps.question" 
      :temporal-info="questionCardProps.temporalInfo" 
      :intermediate-question-text="questionCardProps.intermediateQuestionText"
      :intermediate-temporal-info="questionCardProps.intermediateTemporalInfo"
      :intermediate-graph-data="questionCardProps.graphData"
      :answers="questionCardProps.answers"
      :evidences="questionCardProps.evidences"
      :selected-types="questionCardProps.selectedTypes"
    />
    
    <!-- Answers -->
    <div class="card mt-4">
      <div class="card-header bg-light d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Answer Ranking</h5>
      </div>
      <div class="card-body">
        <div class="row g-3">
          <template v-if="answers.length">
            <div v-for="(answer, index) in answers.slice(0, 5)" 
                 :key="answer.id" 
                 class="col-md-6 col-lg-4">
              <div :class="['card h-100', answer.isCorrect ? 'border-success' : 'border-light', 'shadow-sm']">
                <div class="card-body">
                  <div class="d-flex justify-content-between align-items-center mb-2">
                    <span :class="['badge', answer.isCorrect ? 'bg-success' : 'bg-secondary', 'rounded-pill']">
                      TOP {{ index + 1 }}
                    </span>
                    <span class="badge bg-light text-dark">
                      {{ (answer.score ? answer.score * 100 : 0).toFixed(2) }}%
                    </span>
                  </div>
                  <h6 class="card-title text-truncate" :title="answer.label">
                    <i v-if="answer.isCorrect" class="bi bi-check-circle-fill text-success me-1"></i>
                    {{ answer.label }}
                  </h6>
                  <p class="card-text small text-muted mb-0">
                    ID: {{ answer.id }}
                  </p>
                </div>
              </div>
            </div>
          </template>
          <div v-else class="col-12">
            <div class="alert alert-info mb-0">
              No answer ranking information
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Evidences -->
    <div class="card mt-4">
      <div class="card-header bg-light d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Support Evidence</h5>
      </div>
      <div class="card-body">
        <div class="row g-3">
          <template v-if="candidateEvidences.length">
            <div v-for="(evidence, index) in candidateEvidences.slice(0, 5)" 
                 :key="index" 
                 class="col-12">
              <div :class="['card h-100', evidence.isAnswering ? 'border-success' : 'border-light', 'shadow-sm']">
                <div class="card-body">
                  <div class="d-flex justify-content-between align-items-start mb-2">
                    <div class="d-flex align-items-center">
                      <span :class="['badge', evidence.isAnswering ? 'bg-success' : 'bg-secondary', 'rounded-pill', 'me-2']">
                        Evidence {{ index + 1 }}
                      </span>
                      <span v-if="evidence.isAnswering" class="badge bg-success ms-2">答案证据</span>
                    </div>
                    <div class="d-flex align-items-center">
                      <span class="badge bg-light text-dark me-2">
                        {{ (evidence.score ? evidence.score * 100 : 0).toFixed(2) }}%
                      </span>
                      <span class="badge bg-light text-dark" :title="'Source'">
                        <i :class="getSourceIcon(evidence.source)"></i>
                        {{ getSourceName(evidence.source) }}
                      </span>
                    </div>
                  </div>
                  <p class="card-text mb-0 evidence-text">
                    {{ evidence.evidence_text }}
                  </p>
                </div>
              </div>
            </div>
          </template>
          <div v-else class="col-12">
            <div class="alert alert-info mb-0">
              No support evidence information
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Graphcard -->
    <div class="card mt-4">
      <div class="card-header bg-light d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Knowledge Graph</h5>
      </div>
      <div class="card-body" style="height: 700px;" ref="graphContainer">
        <div ref="chartContainer" style="width: 100%; height: 100%;"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.evidence-text {
  white-space: pre-wrap;
  font-size: 0.9rem;
  line-height: 1.5;
}
</style>