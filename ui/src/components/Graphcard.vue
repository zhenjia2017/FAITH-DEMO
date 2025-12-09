<template>
  <div class="card mt-4">
    <div class="card-header bg-light d-flex justify-content-between align-items-center">
      <h5 class="mb-0 fw-bold">Heterogeneous Answering</h5>
      <button class="btn btn-outline-secondary btn-sm collapse-btn" @click="toggleGraph">
        <i :class="['bi', isCollapsed ? 'bi-chevron-down' : 'bi-chevron-up']"></i>
      </button>
    </div>
    <div
      class="card-body"
      :style="{
        height: isCollapsed ? '0px' : '700px',
        padding: isCollapsed ? '0px' : '16px',
        transition: 'height 0.3s ease'
      }"
    >
      <div ref="chartContainer" style="width: 100%; height: 100%;"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import type { Ref } from 'vue'
import * as echarts from 'echarts'
import type { NodeStyle } from '@/types'

type HighlightSpec =
  | { kind: 'candidate_text'; texts: string[] }
  | { kind: 'answers'; ids: string[] }

const props = withDefaults(defineProps<{
  graphData?: any
  isCollapsed?: boolean

  /** If parent passes index/count via props (recommended zero-based index) */
  panelIndex?: number
  panelCount?: number

  /** If parent provides functions for count/index, use these providers (highest priority) */
  totalProvider?: () => number
  indexProvider?: () => number

  rankedAnswers?: Array<{ id?: string; label?: string }>
  rankedHighlightColor?: string
  rankedMax?: number

  /** If parent explicitly says this is the last panel (lowest priority fallback) */
  isFinal?: boolean

  highlight?: HighlightSpec
  /** For non-final panels, number of evidences highlighted by score */
  evidenceHighlightTopK?: number
}>(), {
  isCollapsed: false,
  panelIndex: 0,
  panelCount: 1,
  rankedAnswers: () => [],
  rankedHighlightColor: '#74A160',
  rankedMax: 5,
  isFinal: false,
  highlight: undefined,
  evidenceHighlightTopK: 5
})

const emit = defineEmits<{
  (e: 'update:isCollapsed', value: boolean): void
}>()

const chartContainer: Ref<HTMLElement | null> = ref(null)
let chart: echarts.ECharts | null = null
const isCollapsed = ref(props.isCollapsed)

watch(() => props.isCollapsed, (v) => { if (v !== undefined) isCollapsed.value = v })

/** Resolve index/count from a single source to avoid 0/1-based ambiguity */
const resolvedCount = computed<number | undefined>(() => {
  try {
    const v = props.totalProvider?.()
    if (typeof v === 'number' && v > 0) return v
  } catch {}
  if (typeof props.panelCount === 'number' && props.panelCount > 0) return props.panelCount
  return undefined
})

const resolvedIndex = computed<number | undefined>(() => {
  try {
    const v = props.indexProvider?.()
    if (typeof v === 'number' && v >= 0) return v
  } catch {}
  if (typeof props.panelIndex === 'number' && props.panelIndex >= 0) return props.panelIndex
  return undefined
})

/** Final-panel decision (single-source rules):
 *  1) If count & index exist, use zero-based: index === count - 1
 *  2) Else if isFinal is true, use isFinal
 *  3) Otherwise treat as not final
 */
const isFinalPanel = computed<boolean>(() => {
  if (resolvedCount.value !== undefined && resolvedIndex.value !== undefined) {
    return resolvedIndex.value === resolvedCount.value - 1
  }
  return !!props.isFinal
})

// Re-render whenever data/highlight basis changes
watch(
  [() => props.graphData, () => props.rankedAnswers, () => props.highlight, isFinalPanel, resolvedCount, resolvedIndex],
  () => { if (props.graphData) updateChart(props.graphData) },
  { deep: true }
)

const initChart = () => {
  if (!chartContainer.value) return
  chart = echarts.init(chartContainer.value)
  window.addEventListener('resize', handleResize as EventListener)
  if (props.graphData) updateChart(props.graphData)
}

const handleResize = (_e?: UIEvent) => chart?.resize()

const toggleGraph = (_e?: MouseEvent) => {
  isCollapsed.value = !isCollapsed.value
  emit('update:isCollapsed', isCollapsed.value)
  setTimeout(() => chart?.resize(), 300)
}

// ---------- Utilities & Styles ----------

const normalizeText = (s: string) =>
  (s ?? '')
    .replace(/\r\n/g, '\n')
    .replace(/\u00A0/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()

// Follow the pie-chart color scheme from App.vue
const getEvidenceColor = (source?: string): string => {
  const colors: Record<string, string> = {
    'kb': '#5470C6',      // blue
    'text': '#91CC75',    // green
    'table': '#FAC858',   // yellow
    'info': '#9A60B4'     // purple
  }
  return colors[source || ''] || '#808080' // default gray
}

const getColor = (type: string, source?: string) => {
  if (type === 'evidence_text') {
    return getEvidenceColor(source)
  }
  if (type === 'wikidata_entity' || type === 'tempinfo') {
    return '#808080' // gray
  }
  return '#808080' // default gray
}

// Generate a darker color variant for emphasis
function darkenColor(hex: string, percent: number = 30): string {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = Math.max(0, Math.min(255, Math.round(((num >> 16) & 0xff) * (1 - percent / 100))))
  const g = Math.max(0, Math.min(255, Math.round(((num >> 8) & 0xff) * (1 - percent / 100))))
  const b = Math.max(0, Math.min(255, Math.round((num & 0xff) * (1 - percent / 100))))
  const toHex = (n: number) => {
    const hex = n.toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }
  return '#' + toHex(r) + toHex(g) + toHex(b)
}

const getNodeStyle = (node: any, totalNodes: number): NodeStyle => {
  const type = node.attributes?.type || 'other'
  const source = node.attributes?.source
  const isAnswer = node.attributes?.is_answer === 'true'
  const isLargeGraph = totalNodes > 100

  const baseColor = getColor(type, source)

  let style: NodeStyle = {
    itemStyle: {
      color: baseColor,
      borderWidth: isLargeGraph ? 1 : 2,
      borderType: 'solid',
      shadowColor: 'rgba(255, 255, 255, 0.2)',
      shadowBlur: isLargeGraph ? 2 : 5,
      opacity: isLargeGraph ? 0.7 : 0.9
    }
  }

  if (isAnswer) {
    style.itemStyle.borderColor = darkenColor(baseColor, 30)
    style.itemStyle.borderWidth = isLargeGraph ? 2 : 4
    style.itemStyle.shadowBlur = isLargeGraph ? 10 : 20
    style.itemStyle.shadowColor = hexToRgba(darkenColor(baseColor, 20), 0.5)
    style.itemStyle.opacity = 1
  }

  if (type === 'evidence_text') {
    style.itemStyle.opacity = isLargeGraph ? 0.6 : 0.85
    style.itemStyle.shadowBlur = isLargeGraph ? 5 : 10
  }

  return style
}

const getNodeSize = (node: any, totalNodes: number) => {
  const type = node.attributes?.type || 'other'
  const isAnswer = node.attributes?.is_answer === 'true'
  const isLargeGraph = totalNodes > 100

  let size = isLargeGraph ? 15 : 30
  switch (type) {
    case 'evidence_text':
      size = isLargeGraph ? 20 : 50
      break
    case 'wikidata_entity':
      size = isLargeGraph ? (isAnswer ? 25 : 18) : (isAnswer ? 60 : 40)
      break
    case 'retrieved_for_entity':
    case 'disambiguation':
      size = isLargeGraph ? 16 : 35
      break
    case 'tempinfo':
      size = isLargeGraph ? 18 : 40
      break
  }
  return size
}

function isQEntity(node?: { attributes?: { wikidata_id?: string } }): boolean {
  const id = node?.attributes?.wikidata_id || ''
  return typeof id === 'string' && id.startsWith('Q')
}

const getNodeSymbol = (
  type?: string,
  source?: string,
  node?: { attributes?: { wikidata_id?: string } }
) => {
  // Evidence nodes use squares
  if (type === 'evidence_text') {
    return 'rect'
  }
  // Entity nodes use circles
  if (type === 'wikidata_entity') {
    return 'circle'
  }
  // Temporal info uses triangles
  if (type === 'tempinfo') {
    return 'triangle'
  }
  // Other types default to circle
  return 'circle'
}

function hexToRgba(hex: string, alpha = 0.45) {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  if (!m) return `rgba(138,75,83,${alpha})`
  const r = parseInt(m[1], 16), g = parseInt(m[2], 16), b = parseInt(m[3], 16)
  return `rgba(${r},${g},${b},${alpha})`
}

const softWrap = (text: string, maxLength = 35) => {
  const parts: string[] = []
  let remaining = text
  while (remaining.length > maxLength) {
    let i = remaining.substring(0, maxLength).lastIndexOf('。')
    if (i === -1) i = remaining.substring(0, maxLength).lastIndexOf(',')
    if (i === -1) i = remaining.substring(0, maxLength).lastIndexOf(' ')
    if (i === -1) i = maxLength
    parts.push(remaining.substring(0, i + 1).trim())
    remaining = remaining.substring(i + 1).trim()
  }
  if (remaining) parts.push(remaining)
  return parts.join('\n')
}

const formatTooltip = (data: any) => {
  const attrs = data.attributes || {}
  const score = parseFloat(attrs.score || 0).toFixed(3)
  const type = attrs.type || 'Unknown'
  const source = attrs.source

  const displayType = (() => {
    if (type === 'wikidata_entity') return isQEntity(data) ? 'Entity' : 'Temporal Info'
    if (type === 'tempinfo') return 'Temporal Info'
    if (type === 'evidence_text') return 'Evidence'
    return type
  })()

  if (type === 'evidence_text') {
    return [
      'Name:',
      `
      <div style="
        padding:8px;margin:5px 0;background:#f8f9fa;border-radius:4px;
        line-height:1.4;max-width:1000px;white-space:pre-wrap;word-break:break-word;">
        ${softWrap(data.name)}
      </div>`,
      `Type: ${displayType}`,
      `Source: ${source || 'Unknown'}`,
      `Score: ${score}`,
    ].join('<br>')
  }

  const extra: string[] = []
  Object.entries(attrs).forEach(([k, v]) => {
    if (!['type', 'label', 'temporal_value', 'wikidata_id', 'is_answer', 'entity_type', 'Entity Type', 'Is Answer'].includes(k)) {
      extra.push(`${k}: ${v}`)
    }
  })

  if (type === 'wikidata_entity') {
    return [
      `Name: ${data.name}`,
      `Type: ${displayType}`,
      attrs.wikidata_id && attrs.wikidata_id.startsWith('Q')
        ? `Wikidata ID: ${attrs.wikidata_id}`
        : `Temporal Value: ${attrs.wikidata_id || 'Unknown'}`,
      ...extra
    ].join('<br>')
  }

  return [
    `Name: ${data.name}`,
    `Type: ${displayType}`,
    ...extra
  ].join('<br>')
}

// ---------- Highlight matching ----------
interface Evidence {
  normText: string
  score: number
}

type HighlightSets =
  | { mode: 'candidate_text'; texts: Set<string>; ids: Set<string>; labels: Set<string> }
  | { mode: 'answers';        texts: Set<string>; ids: Set<string>; labels: Set<string> }

function buildHighlightSets(data: any): HighlightSets {
  // 1) Explicit highlight takes priority
  if (props.highlight?.kind === 'candidate_text') {
    const texts = new Set<string>((props.highlight.texts || []).map(normalizeText))
    return { mode: 'candidate_text', texts, ids: new Set<string>(), labels: new Set<string>() }
  }
  if (props.highlight?.kind === 'answers') {
    const ids = new Set<string>((props.highlight.ids || []).map(String))
    return { mode: 'answers', texts: new Set<string>(), ids, labels: new Set<string>() }
  }

  // 2) No highlight provided: final panel emphasizes entity answers
  if (isFinalPanel.value) {
    const topAnswers = (props.rankedAnswers || []).slice(0, props.rankedMax)
    const ids    = new Set<string>(topAnswers.map(a => String(a?.id || '')).filter(Boolean))
    const labels = new Set<string>(topAnswers.map(a => String(a?.label || '')).filter(Boolean))
    return { mode: 'answers', texts: new Set<string>(), ids, labels }
  }

  // 3) Other panels emphasize evidences (top K by score)
  const K = Math.max(1, Number(props.evidenceHighlightTopK) || 5)
  const evidences: Evidence[] = (data?.nodes || [])
    .filter((n: any) => n?.attributes?.type === 'evidence_text')
    .map((n: any): Evidence => {
      const raw =
        n?.attributes?.evidence_text ??
        n?.attributes?.text ??
        n?.attributes?.content ??
        n?.name ?? ''
      return {
        normText: normalizeText(String(raw)),
        score: Number(n?.attributes?.score ?? 0)
      }
    })
    .filter((e: Evidence) => e.normText.length > 0)
    .sort((a: Evidence, b: Evidence) => b.score - a.score)
    .slice(0, K)

  const texts = new Set<string>(evidences.map((e: Evidence) => e.normText))
  return { mode: 'candidate_text', texts, ids: new Set<string>(), labels: new Set<string>() }
}

function isNodeHighlightedByCandidate(node: any, texts: Set<string>): boolean {
  if (node?.attributes?.type !== 'evidence_text') return false
  const raw =
    node?.attributes?.evidence_text ??
    node?.attributes?.text ??
    node?.attributes?.content ??
    node?.name ?? ''
  const norm = normalizeText(String(raw))
  return texts.has(norm)
}

function isNodeHighlightedByAnswers(node: any, ids: Set<string>, labels: Set<string>): boolean {
  if (node?.attributes?.type !== 'wikidata_entity') return false
  const nodeId = String(node?.attributes?.wikidata_id || node?.id || '')
  if (nodeId && ids.has(nodeId)) return true
  const name = String(node?.name || '')
  if (name && labels.has(name)) return true
  return false
}

// ---------- Render ----------

const updateChart = (data: any) => {
  if (!chart || !data) return

  const totalNodes = data.nodes?.length || 0
  const evidenceTextCount = data.nodes?.filter((n: any) => n.attributes?.type === 'evidence_text').length || 0

  const hiSpec: HighlightSets = buildHighlightSets(data)
  // Highlight colors derive from each node's base color
  const highlightedGraphNodeIdSet = new Set<string>()
  const nodeHighlightColors = new Map<string, string>() // store per-node highlight color

  // Tooltip type fix
  const tooltipFormatter: echarts.TooltipComponentOption['formatter'] = (params) => {
    const p: any = Array.isArray(params) ? params[0] : params
    return p?.dataType === 'edge' ? '' : formatTooltip(p?.data)
  }

  const option: echarts.EChartsOption = {
    backgroundColor: '#f8f9fb',
    animationDurationUpdate: 3000,
    animationEasingUpdate: 'quinticInOut',
    title: {
      subtext: `Nodes (Entity / Temporal Info + Sources): ${totalNodes}\n\nEvidence Texts: ${evidenceTextCount}`,
      left: 30,
      bottom: 20,
      textStyle: { fontSize: 14, fontWeight: 'normal', color: '#2c3e50' },
      subtextStyle: { color: '#666', fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'item',
      formatter: tooltipFormatter,
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#eee',
      borderWidth: 1,
      padding: [10, 15],
      textStyle: { color: '#2c3e50' }
    },
    legend: {
      data: [
        { name: 'Entity',        icon: 'circle', itemStyle: { color: '#808080' } },
        { name: 'Temporal Info', icon: 'triangle', itemStyle: { color: '#808080' } },
        { name: 'KB',    icon: 'rect', itemStyle: { color: '#5470C6' } },
        { name: 'Text',  icon: 'rect', itemStyle: { color: '#91CC75' } },
        { name: 'Table', icon: 'rect', itemStyle: { color: '#FAC858' } },
        { name: 'Infobox', icon: 'rect', itemStyle: { color: '#9A60B4' } }
      ],
      left: 30,
      top: 60,
      orient: 'vertical',
      textStyle: { color: '#2c3e50' },
      itemWidth: 16,
      itemHeight: 16,
      itemGap: 10,
      formatter: (name: string) => {
        const counts = {
          'Entity':        data.nodes.filter((n: any) => n.attributes?.type === 'wikidata_entity' && isQEntity(n)).length,
          'Temporal Info': data.nodes.filter((n: any) =>
            (n.attributes?.type === 'wikidata_entity' && !isQEntity(n)) ||
            (n.attributes?.type === 'tempinfo')
          ).length,
          'KB':      data.nodes.filter((n: any) => n.attributes?.source === 'kb').length,
          'Text':    data.nodes.filter((n: any) => n.attributes?.source === 'text').length,
          'Table':   data.nodes.filter((n: any) => n.attributes?.source === 'table').length,
          'Infobox': data.nodes.filter((n: any) => n.attributes?.source === 'info').length
        }
        return `${name} (${counts[name as keyof typeof counts] || 0})`
      },
      selectedMode: 'multiple'
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: data.nodes.map((node: any) => {
        let categoryIndex = 0
        const type = node.attributes?.type
        const source = node.attributes?.source

        if (type === 'wikidata_entity')       categoryIndex = isQEntity(node) ? 0 : 1
        else if (type === 'tempinfo')         categoryIndex = 1
        else if (source === 'kb')             categoryIndex = 2
        else if (source === 'text')           categoryIndex = 3
        else if (source === 'table')          categoryIndex = 4
        else if (source === 'info')           categoryIndex = 5

        const nodeColor = getColor(type, source)
        // Determine symbol by category: Temporal Info uses triangles
        let nodeSymbol = getNodeSymbol(node.attributes?.type, node.attributes?.source, node)
        if (categoryIndex === 1) { // Temporal Info category
          nodeSymbol = 'triangle'
        }
        
        const base: any = {
          ...node,
          symbolSize: getNodeSize(node, data.nodes.length),
          symbol: nodeSymbol,
          ...getNodeStyle(node, data.nodes.length),
          category: categoryIndex,
          label: {
            show: node.attributes?.type === 'evidence_text' ? (data.nodes.filter((n: any) => n.attributes?.type === 'evidence_text').length < 1) : true,
            position: 'right',
            formatter: () => {
              if (node.attributes?.type === 'tempinfo' && node.attributes?.temporal_value) {
                return node.attributes.temporal_value
              }
              return node.name
            },
            fontSize: node.attributes?.is_answer === 'true' ? 14 : 12,
            color: '#2c3e50'
          }
        }

        // Highlight rules
        const hit = (hiSpec.mode === 'candidate_text')
          ? isNodeHighlightedByCandidate(node, hiSpec.texts)
          : isNodeHighlightedByAnswers(node, hiSpec.ids, hiSpec.labels)

        if (hit) {
          if (node?.id != null) {
            highlightedGraphNodeIdSet.add(String(node.id))
            // Store node highlight color (darker variant of its base color)
            nodeHighlightColors.set(String(node.id), darkenColor(nodeColor, 30))
          }
          base.symbolSize = Math.round(base.symbolSize * 1.15)
          const highlightColor = darkenColor(nodeColor, 30)
          base.itemStyle = {
            ...base.itemStyle,
            borderColor: highlightColor,
            borderWidth: 5,
            shadowColor: hexToRgba(highlightColor, 0.6),
            shadowBlur: 22,
            opacity: 1
          }
          base.label = { ...base.label, fontWeight: 'bold' }
        }

        return base
      }),
      links: data.links.map((link: any) => {
        const from = String(link.source)
        const to   = String(link.target)
        const touchHi = highlightedGraphNodeIdSet.has(from) || highlightedGraphNodeIdSet.has(to)

        const baseWidth = Math.max(1, Math.min(2.5, Math.pow(link.value || 1, 0.6) * 1.5))

        // If an edge touches a highlighted node, reuse that node's highlight color
        let highlightLinkColor = '#74A160' // default highlight color
        if (touchHi) {
          const fromColor = nodeHighlightColors.get(from)
          const toColor = nodeHighlightColors.get(to)
          highlightLinkColor = fromColor || toColor || highlightLinkColor
        }

        return {
          ...link,
          lineStyle: touchHi
            ? { width: Math.max(baseWidth, 3.5), color: hexToRgba(highlightLinkColor, 0.85), curveness: 0.12 }
            : {
                width: 2,
                color: link.value > 0.8 ? 'rgba(50, 50, 50, 0.3)'
                     : link.value > 0.5 ? 'rgba(50, 50, 50, 0.3)'
                     : link.value > 0.3 ? 'rgba(50, 50, 50, 0.3)'
                     : 'rgba(50, 50, 50, 0.3)',
                curveness: 0.1
              },
          silent: true
        }
      }),
      categories: [
        { name: 'Entity',        itemStyle: { color: '#808080' } },
        { name: 'Temporal Info', itemStyle: { color: '#808080' } },
        { name: 'KB',            itemStyle: { color: '#5470C6' } },
        { name: 'Text',          itemStyle: { color: '#91CC75' } },
        { name: 'Table',         itemStyle: { color: '#FAC858' } },
        { name: 'Infobox',       itemStyle: { color: '#9A60B4' } }
      ],
      force: {
        repulsion: [50, 500],
        edgeLength: [50, 200],
        gravity: 0.1
      },
      emphasis: {
        focus: 'adjacency',
        scale: true,
        lineStyle: { width: 4 },
        label: {
          show: true,
          fontSize: 16,
          backgroundColor: 'rgba(255,255,255,0.95)',
          padding: [4, 8],
          borderRadius: 4
        },
        itemStyle: {
          shadowBlur: 12,
          shadowColor: 'rgba(0, 0, 0, 0.2)',
          borderWidth: 2
        }
      },
      nodeScaleRatio: 0.6,
      focusNodeAdjacency: true,
      roam: true,
      draggable: true
    }]
  }

  // Important: do not merge options to avoid stale highlight state
  chart.setOption(option, true)
}

onMounted(() => initChart())
onUnmounted(() => {
  window.removeEventListener('resize', handleResize as EventListener)
  chart?.dispose()
})
</script>

<style scoped>
.card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
  margin-bottom: 1.5rem;
  border-radius: 8px;
  overflow: hidden;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}
.card-body {
  transition: height 0.3s ease-in-out;
  overflow: hidden;
}
.collapse-btn {
  transition: all 0.3s ease;
}
.collapse-btn.collapsed {
  transform: rotate(180deg);
}
</style>
