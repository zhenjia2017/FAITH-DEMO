export interface CurrentData {
    question: string
    temporalInfo: {
      entity?: string
      category?: string
      relation?: string
      answerType?: string
      temporalSignal?: string
      temporalValues?: any[][]
    }
    rankedAnswers: Array<{
      label: string
      id: string
      score: number
      isCorrect: boolean
    }>
    evidences: Array<{
      text: string
      source: string
      score: number
      isAnswering: boolean
      url?: string
    }>
    graphData: any
    initialEvidencesLength: number
    initialEvidencesSource: Record<string, number>
    prunedEvidencesLength: number
    prunedEvidencesSource: Record<string, number>
    topkEvidencesLength: number
    topkEvidencesSource: Record<string, number>
    candidateGraphData?: { 
      nodes: Array<{ id: string | null, name: string | null, attributes: Record<string,string> }>; 
      links: Array<{ source: string | null, target: string | null, value: number, label: string | null }>; 
      question: string;
    } | null;
  }
export interface Evidence {
  text:       string;
  source:     string;
  score:      number;
  isAnswering: boolean;
  url?: string;
}
 export interface NodeStyle {
    itemStyle: {
      color: string
      borderWidth: number
      borderType: string
      shadowColor: string
      shadowBlur: number
      opacity: number
      borderColor?: string
    }
  }

export interface TemporalInfo {
  entity?: string
  category?: string
  relation?: string
  answerType?: string
  temporalSignal?: string
  temporalValues?: any[][]
}
export interface GraphNode {
  id:   string | null;
  name: string | null;
  attributes: Record<string,string>;
}

export interface GraphLink {
  source: string | null;
  target: string | null;
  value:  number;
  label:  string | null;
}

/** 对应 GEXF 解析后的一张图的数据格式 */
export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  question?: string;
}