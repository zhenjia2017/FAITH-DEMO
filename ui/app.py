from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
import json
import networkx as nx
import xml.etree.ElementTree as ET
import logging
import traceback
import xml.dom.minidom
import os
import requests
import re
import codecs

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
# 启用CORS，允许前端访问
CORS(app)

# 创建蓝图
bp = Blueprint('api', __name__, url_prefix='/api')

def format_tempinfo(temp_info):
    """格式化时间信息，只处理第二类时间信息（年份标签）"""
    if not temp_info:
        return ""
    
    # 如果是列表，提取所有时间值
    if isinstance(temp_info, list) and len(temp_info) >= 2:
        # 只处理第二类时间信息
        second_type_info = temp_info[1]
        
        # 收集所有年份标签
        time_labels = set()
        for item in second_type_info:
            if isinstance(item, list) and len(item) == 2:
                label, timestamp = item
                if isinstance(label, str) and not 'T' in label:
                    time_labels.add(label)
        
        # 将年份转换为整数进行排序
        years = []
        other_labels = []
        for label in time_labels:
            if label.isdigit() and len(label) == 4:
                years.append(int(label))
            else:
                other_labels.append(label)
        
        sorted_years = sorted(years)
        
        if not sorted_years and not other_labels:
            return ""
        elif len(sorted_years) == 1 and not other_labels:
            # 只有一个年份
            return str(sorted_years[0])
        elif len(sorted_years) > 1 and not other_labels:
            # 检查是否是连续的年份范围
            start_year = sorted_years[0]
            end_year = sorted_years[-1]
            if end_year - start_year == len(sorted_years) - 1:
                # 连续的年份范围，使用短横线连接
                return f"{start_year}-{end_year}"
            else:
                # 不连续的年份，用逗号分隔
                return ', '.join(map(str, sorted_years))
        else:
            # 包含非年份的时间标签，全部用逗号分隔
            all_times = [str(y) for y in sorted_years] + other_labels
            return ', '.join(all_times)
    
    # 如果是字符串，直接返回处理后的结果
    return str(temp_info).strip('[]')

def format_xml(xml_string):
    """格式化XML字符串"""
    try:
        # 使用minidom解析字符串
        dom = xml.dom.minidom.parseString(xml_string)
        # 返回格式化的XML字符串，缩进为2个空格
        return dom.toprettyxml(indent='  ')
    except Exception as e:
        logger.error(f"Error formatting XML: {str(e)}")
        return xml_string

def json_to_gexf(json_data):
    """将JSON数据转换为GEXF格式的XML字符串，支持读取任意数量的 iterative_{n}_scored_evidences 字段"""
    try:
        import re

        G = nx.Graph()
        entity_nodes = {}       # 存储所有实体节点
        evidence_nodes = {}     # 存储证据节点
        label_to_wikidataID = {}  # 存储标签到 wikidataID 的映射
        current_id = 0

        # 校验输入
        if not isinstance(json_data, list) or len(json_data) == 0:
            raise ValueError("Invalid JSON data format")

        # 只使用第一个元素（原版逻辑）
        item = json_data[0]

        # 提取 Question 和 temporal
        question = item.get("Question", "")
        structured_temporal = item.get("structured_temporal_form", {})

        # 提取答案 ID 列表
        answers = item.get("answers") or []
        answer_ids = {a.get("id","") for a in answers if isinstance(a, dict) and a.get("id")}


        logger.debug(f"Processing question: {question}")
        logger.debug(f"Structured temporal information: {structured_temporal}")
        logger.debug(f"Found {len(answer_ids)} answer IDs")

        # 设置图属性
        G.graph['question'] = question
        G.graph['structured_temporal'] = json.dumps(structured_temporal)

        # 创建 XML 根结构
        root = ET.Element('gexf', xmlns="http://www.gexf.net/1.2draft", version="1.2")
        graph = ET.SubElement(root, 'graph', mode="static", defaultedgetype="directed")
        graph.set('question', question)
        graph.set('structured_temporal', json.dumps(structured_temporal))

        # 收集所有 evidence：先拿所有 iterative_n_scored_evidences，再加 candidate_evidences
        pattern = re.compile(r'^iterative_(\d+)_scored_evidences$')
        full_evidences = []
        for k, v in item.items():
            if pattern.match(k) and isinstance(v, list):
                full_evidences.extend(v)
        full_evidences.extend(item.get("candidate_evidences", []))

        # --- 第一遍遍历：收集所有 wikidata_entities 节点 ---
        for evidence in full_evidences:
            if not isinstance(evidence, dict):   # ← 加这一行
                continue
            entities = evidence.get("wikidata_entities") or []  # ← 新增 or []
            if not isinstance(entities, list):   # ← 新增
                continue
            for entity in evidence.get("wikidata_entities", []):
                if not isinstance(entity, dict):  # 不是字典就跳过
                    continue
                eid = entity.get("id", "")
                label = entity.get("label", "")
                if not eid or not label:
                    continue
                t = entity.get("type") or {}     # ← 防 None
                entity_type = t.get("label", "")
                # 记录映射
                label_to_wikidataID[label] = eid
                if eid not in entity_nodes:
                    node_id = f"n{current_id}"
                    current_id += 1
                    entity_nodes[eid] = {
                        "node_id": node_id,
                        "label": label,
                        "type": "wikidata_entity",
                        "wikidata_id": eid,
                        "entity_type": (entity.get("type") or {}).get("label", ""),
                        "is_answer": eid in answer_ids
                    }
                    G.add_node(node_id, **entity_nodes[eid])

        # --- 第二遍遍历：为每条证据创建节点并连边 ---
        for evidence in full_evidences:
            if not isinstance(evidence, dict):   # ← 加这一行
                continue
            text = evidence.get("evidence_text", "")
            if not text:
                continue
            node_id = f"n{current_id}"
            current_id += 1
            ev_meta = {
                "node_id": node_id,
                "label": text,
                "type": "evidence_text",
                "source": evidence.get("source", "unknown"),
                "score": evidence.get("score", 1.0),
                "is_answering": evidence.get("is_answering_evidence", False)
            }
            evidence_nodes[text] = ev_meta
            G.add_node(node_id, **ev_meta)
            # 连接到实体
            entities = evidence.get("wikidata_entities") or []  # ← 新增
            if not isinstance(entities, list):   # ← 新增
                continue
            for entity in evidence.get("wikidata_entities", []):
                if not isinstance(entity, dict):  # 不是字典就跳过
                    continue
                eid = entity.get("id", "")
                if eid in entity_nodes:
                    G.add_edge(
                        node_id,
                        entity_nodes[eid]["node_id"],
                        weight=evidence.get("score", 1.0),
                        label="supports"
                    )

        # # --- 处理结构化时间信息 ---
        # if structured_temporal:
        #     temporal_values = []
        #     for rng in structured_temporal.get("temporal_value", []):
        #         if isinstance(rng, list) and len(rng) == 2:
        #             temporal_values.append(rng)
        #     temporal_node_id = f"n{current_id}"
        #     current_id += 1
        #     temp_meta = {
        #         "node_id": temporal_node_id,
        #         "label": f"时间信息: {structured_temporal.get('temporal_signal','')}",
        #         "type": "tempinfo",
        #         "category": structured_temporal.get("category",""),
        #         "answer_type": structured_temporal.get("answer_type",""),
        #         "temporal_signal": structured_temporal.get("temporal_signal",""),
        #         "temporal_value": json.dumps(temporal_values)
        #     }
        #     G.add_node(temporal_node_id, **temp_meta)
        #     ent_label = structured_temporal.get("entity","")
        #     if ent_label in label_to_wikidataID:
        #         eid = label_to_wikidataID[ent_label]
        #         if eid in entity_nodes:
        #             G.add_edge(
        #                 temporal_node_id,
        #                 entity_nodes[eid]["node_id"],
        #                 weight=1.0,
        #                 label=structured_temporal.get("relation","")
        #             )

        # --- 定义节点属性 ---
        attr_list = [
            ('type','string'),('wikidata_id','string'),('entity_type','string'),
            ('is_answer','boolean'),('source','string'),('score','float'),
            ('is_answering','boolean'),('category','string'),
            ('answer_type','string'),('temporal_signal','string'),
            ('temporal_value','string')
        ]
        attributes_el = ET.SubElement(graph, 'attributes', **{'class':'node'})
        for idx, (title, tpe) in enumerate(attr_list):
            ET.SubElement(attributes_el, 'attribute', id=str(idx), title=title, type=tpe)

        # --- 序列化节点 ---
        nodes_el = ET.SubElement(graph, 'nodes')
        for node_id in G.nodes():
            data = G.nodes[node_id]
            n_el = ET.SubElement(nodes_el, 'node', id=node_id, label=data.get('label',''))
            av = ET.SubElement(n_el, 'attvalues')
            for idx, (title, _) in enumerate(attr_list):
                if title in data:
                    ET.SubElement(av, 'attvalue', **{'for':str(idx), 'value':str(data[title])})

        # --- 序列化边 ---
        edges_el = ET.SubElement(graph, 'edges')
        for i, (src, tgt, d) in enumerate(G.edges(data=True)):
            ed = ET.SubElement(edges_el, 'edge', id=f"e{i}", source=src, target=tgt, weight=str(d.get('weight',1.0)))
            if 'label' in d:
                ed.set('label', d['label'])

        # 返回格式化后的 GEXF 字符串
        xml_str = ET.tostring(root, encoding='unicode')
        return format_xml(xml_str)

    except Exception:
        logger.error("Error in json_to_gexf", exc_info=True)
        raise

import string

# 识别常见 mojibake 片段（UTF-8 被按 latin-1/cp1252 解码后出现的痕迹）
_MOJIBAKE_PAT = re.compile(r'(?:Ã.|Â.|â..)')
def _looks_like_mojibake(s: str) -> bool:
    return bool(_MOJIBAKE_PAT.search(s))

def _printable_ratio(s: str) -> float:
    if not s:
        return 1.0
    allow_ws = {'\r', '\n', '\t'}
    allow_extra = {"—", "–", "’", "“", "”", "…", "•", "™", "©", "®"}
    good = sum(1 for ch in s if ch.isprintable() or ch in allow_ws or ch in allow_extra)
    return good / len(s)

def _fix_mojibake_chain(s: str, max_rounds: int = 2) -> str:
    if not isinstance(s, str):
        return s
    t = s
    for _ in range(max_rounds):
        try:
            cand = t.encode("latin-1").decode("utf-8")
        except Exception:
            break
        if _looks_like_mojibake(t) and not _looks_like_mojibake(cand):
            t = cand
        elif _printable_ratio(cand) >= _printable_ratio(t):
            t = cand
        else:
            break
    return t

# 匹配“非法/悬空的反斜杠”，以免 unicode_escape 报错
_INVALID_ESCAPE_BACKSLASH = re.compile(
    r'\\(?!u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|x[0-9a-fA-F]{2}|[abfnrtv\\\'"])'
)
# 判断是否真的含有需要解析的转义
_NEEDS_UNICODE_ESC = re.compile(
    r'\\(?:u[0-9a-fA-F]{4}|U[0-9a-fA-F]{8}|x[0-9a-fA-F]{2}|[abfnrtv\\\'"])'
)

def _safe_decode_unicode_escapes(s: str) -> str:
    if not isinstance(s, str):
        return s
    if _looks_like_mojibake(s):
        s = _fix_mojibake_chain(s)
    if not _NEEDS_UNICODE_ESC.search(s):
        return s

    # 保护非法/悬空的反斜杠，避免 decode 报错
    protected = _INVALID_ESCAPE_BACKSLASH.sub(r'\\\\', s)

    try:
        return codecs.decode(protected.encode("utf-8"), "unicode_escape")
    except UnicodeDecodeError:
        return s

def _decode_unicode_escapes(obj):
    if isinstance(obj, str):
        return _safe_decode_unicode_escapes(obj)
    elif isinstance(obj, list):
        return [_decode_unicode_escapes(v) for v in obj]
    elif isinstance(obj, dict):
        return {k: _decode_unicode_escapes(v) for k, v in obj.items()}
    else:
        return obj


@bp.route('/convert', methods=['POST'])
def convert():
    """将JSON数据转换为GEXF格式"""
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        logger.debug("Received JSON data for conversion")
        gexf_data = json_to_gexf(json_data)
        logger.debug("Successfully converted JSON to GEXF")
        
        return jsonify({"gexf": gexf_data})
    except Exception as e:
        logger.error(f"Error in convert route: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@bp.route('/process-question', methods=['POST'])
def process_question():
    pattern = re.compile(r'^iterative_(\d+)_scored_evidences$')

    # 1) 解析参数（仅 POST）
    data       = request.get_json() or {}
    query      = (data.get('question') or '').strip()
    es_method  = data.get('es_method')
    ha_method  = data.get('ha_method')
    benchmark  = data.get('benchmark')
    sources    = data.get('sources')
    iteration  = data.get('iteration')                 # 允许 0 | 1 | 2 | 3
    gnn_max_output_evidences = data.get('gnn_max_output_evidences')  # 期望 3 个数
    faith_or_unfaith = (data.get('faith_or_unfaith') or '').strip().lower()
    if faith_or_unfaith not in ('faith', 'unfaith'):
        tp = (data.get('temporalPruning') or 'yes').strip().lower()
        faith_or_unfaith = 'faith' if tp == 'yes' else 'unfaith'

    if not query:
        return jsonify({'error': 'Question parameter not provided'}), 400

    # 2) 调用 FAITH 后端 /answer 接口
    try:
        payload = {
            'question':                query,
            'es_method':               es_method,
            'ha_method':               ha_method,
            'benchmark':               benchmark,
            'sources':                 sources,
            'iteration':               iteration,
            'gnn_max_output_evidences': gnn_max_output_evidences,
            'faith_or_unfaith':        faith_or_unfaith,
        }

        resp = requests.post(
            'http://localhost:7899/answer',
            json=payload,
            timeout=(5, None)
        )
        resp.raise_for_status()
        matched = resp.json()
        matched = _decode_unicode_escapes(matched)
    except Exception as e:
        logger.error(f'调用 FAITH 后端失败: {e}\n{traceback.format_exc()}')
        return jsonify({'error': 'Backend call failed', 'details': str(e)}), 502

    # 为了复用下面对 items 的循环，把 matched 放进一个列表
    items = [matched]

    # 3) 遍历的对象是 items 而不是从文件读来的
    matched_item = None
    matched_question = None

    for item in items:
        orig_q = item.get('Question', '') or item.get('question', '')
        if query.lower() in orig_q.lower():
            matched_item = item
            matched_question = orig_q
            break

        for iq in item.get('intermediate_question_pipeline_result', []):
            iq_text = iq.get('question', '')
            if query.lower() in iq_text.lower():
                matched_item = item
                matched_question = iq_text
                break
        if matched_item:
            break

    if not matched_item:
        return jsonify({
            'error': 'No matches were found in the data returned by the backend',
            'message': 'Please try again'
        }), 404
    
    # 构造返回结果
    result = {
        'success': True,
        'sourceFile': 'example.json',
        'question': matched_question,
        'matchScore': 1.0
    }

    # 时间信息
    if 'structured_temporal_form' in matched:
        ti = matched['structured_temporal_form']
        result['temporalInfo'] = {
            'entity': ti.get('entity', ''),
            'category': ti.get('category', ''),
            'relation': ti.get('relation', ''),
            'answerType': ti.get('answer_type', ''),
            'temporalSignal': ti.get('temporal_signal', ''),
            'temporalValues': ti.get('temporal_value', [])
        }

    # 答案
    if 'ranked_answers' in matched:
        answers = []
        for ra in matched['ranked_answers']:
            ans = ra.get('answer', {}).copy()
            orig_score = ra.get('score', 0)
            ans['score'] = orig_score
            ans['rank'] = ra.get('rank', 0)
            answers.append(ans)
        result['answers'] = answers
    elif 'answers' in matched:
        result['answers'] = matched['answers']

    # 证据
    if 'candidate_evidences' in matched:
        result['candidateEvidences'] = matched['candidate_evidences']

    # 中间问题
    intermediate = matched.get('intermediate_question_pipeline_result') or []
    if intermediate:
        result['intermediateQuestions'] = intermediate

        all_intermediate_gexfs = []
        for iq in intermediate:
            # 找出所有 iterative_x_scored_evidences
            keys = [
                k for k, v in iq.items()
                if pattern.match(k) and isinstance(v, list)
            ]
            keys.sort(key=lambda k: int(pattern.match(k).group(1)))

            # 把每个组，以及最后的前 5 条 candidate_evidences 都包装进 GEXF
            groups = [iq[k] for k in keys]
            if isinstance(iq.get('candidate_evidences'), list):
                groups.append(iq['candidate_evidences'][:5])

            for group in groups:
                wrapper = [{
                    'Question':                 iq.get('question', matched_question),
                    'structured_temporal_form': iq.get('structured_temporal_form', matched.get('structured_temporal_form', {})),
                    'answers':                  iq.get('answers', matched.get('answers', [])),
                    'candidate_evidences':      group
                }]
                try:
                    all_intermediate_gexfs.append(json_to_gexf(wrapper))
                except Exception as e:
                    logger.error(f"Create intermediate iterative GEXF fail: {e}")

        if all_intermediate_gexfs:
            result['iterativeScoredIntermediateEvidencesGexf'] = all_intermediate_gexfs

    # 其他可选字段（问题理解、RAG 答案等）
    for key in ('question_understanding', 'deepseek_rag_answer'):
        if key in matched:
            camel = ''.join([part.capitalize() for part in key.split('_')])
            result[camel[0].lower() + camel[1:]] = matched[key]

    # 生成 GEXF
    try:
        result['gexf'] = json_to_gexf([matched])
    except Exception as e:
        result['gexfError'] = str(e)
    
    # 证据统计字段
    if 'initial_evidences_length' in matched:
        result['initial_evidences_length'] = matched.get('initial_evidences_length', 0)
    if 'initial_evidences_source' in matched:
        result['initial_evidences_source'] = matched.get('initial_evidences_source', {})
    if 'pruned_evidences_length' in matched:
        result['pruned_evidences_length'] = matched.get('pruned_evidences_length', 0)
    if 'pruned_evidences_source' in matched:
        result['pruned_evidences_source'] = matched.get('pruned_evidences_source', {})
    if 'topk_evidences_length' in matched:
        result['topk_evidences_length'] = matched.get('topk_evidences_length', 0)
    if 'topk_evidences_source' in matched:
        result['topk_evidences_source'] = matched.get('topk_evidences_source', {})

    # Candidate_evidences 抓取
    if isinstance(matched.get('candidate_evidences'), list):
        wrapper = [{
            'Question': matched_question,
            'structured_temporal_form': matched.get('structured_temporal_form', {}),
            'answers': matched.get('answers', []),
            'candidate_evidences': matched['candidate_evidences']
        }]
        try:
            result['candidateEvidencesGexf'] = json_to_gexf(wrapper)
        except Exception as e:
            logger.error(f"Create candidate_evidences GEXF fail: {e}")

    result['candidateEvidences'] = matched.get('candidate_evidences', [])

    # 先按序号抓所有 iterative_x_scored_evidences
    iterative_keys = [
        k for k, v in matched.items()
        if pattern.match(k) and isinstance(v, list)
    ]
    iterative_keys.sort(key=lambda k: int(pattern.match(k).group(1)))

    evidence_groups = []
    for key in iterative_keys:
        evidence_groups.append(matched[key])
    # 最后把 candidate_evidences 的前 5 条也当一组
    if isinstance(matched.get('candidate_evidences'), list):
        evidence_groups.append(matched['candidate_evidences'][:5])

    iterative_gexfs = []
    for group in evidence_groups:
        wrapper = [{
            'Question': matched_question,
            'structured_temporal_form': matched.get('structured_temporal_form', {}),
            'answers': matched.get('answers', []),
            'candidate_evidences': group
        }]
        try:
            iterative_gexfs.append(json_to_gexf(wrapper))
        except Exception as e:
            logger.error(f"Create iterative GEXF fail: {e}")
    if iterative_gexfs:
        result['iterativeScoredEvidencesGexf'] = iterative_gexfs
    
    return jsonify(result)




# 添加根路由，直接提供问题分析页面
@app.route('/')
def index():
    return app.send_static_file('question_analyzer.html')

# 注册蓝图
app.register_blueprint(bp)

# 主程序入口
if __name__ == '__main__':
    app.run(debug=True, port=5001, host="0.0.0.0") 
