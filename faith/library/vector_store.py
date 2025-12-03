import os
import json
import faiss
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union

logger = logging.getLogger(__name__)

class VectorStore:
    """
    向量存储类，用于存储和搜索文档嵌入
    """
    
    def __init__(
        self,
        index_path: Optional[str] = None,
        dimension: int = 768,
        index_type: str = "Flat",
        metric: str = "inner_product",
        **kwargs
    ):
        """
        初始化向量存储
        
        Args:
            index_path: 索引文件路径，如果提供，则加载现有索引
            dimension: 嵌入向量维度
            index_type: 索引类型，支持 "Flat"、"IVF"、"HNSW"
            metric: 距离度量，支持 "inner_product"、"l2"
            **kwargs: 其他参数
        """
        self.index_path = index_path
        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric
        
        # 存储文档和ID的映射
        self.doc_ids = []
        self.doc_texts = []
        self.doc_metadata = []
        
        # 初始化空索引
        self.index = None
        
        # 加载或创建索引
        if index_path and os.path.exists(index_path):
            self._load_index()
        else:
            self._create_index()
    
    def _create_index(self):
        """
        创建新的 FAISS 索引
        """
        try:
            logger.info(f"Creating new FAISS index with dimension {self.dimension}")
            
            # 选择距离度量
            if self.metric == "inner_product":
                metric_type = faiss.METRIC_INNER_PRODUCT
            elif self.metric == "l2":
                metric_type = faiss.METRIC_L2
            else:
                raise ValueError(f"Unsupported metric type: {self.metric}")
            
            # 创建索引
            if self.index_type == "Flat":
                self.index = faiss.IndexFlatIP(self.dimension) if self.metric == "inner_product" else faiss.IndexFlatL2(self.dimension)
            elif self.index_type == "IVF":
                # IVF索引需要数据进行训练，这里先创建一个基础索引
                quantizer = faiss.IndexFlatIP(self.dimension) if self.metric == "inner_product" else faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100, metric_type)
                # 注意：IVF 索引在添加向量前需要训练
            elif self.index_type == "HNSW":
                self.index = faiss.IndexHNSWFlat(self.dimension, 32, metric_type)
            else:
                raise ValueError(f"Unsupported index type: {self.index_type}")
            
            logger.info(f"Created {self.index_type} index with {self.metric} metric")
            
        except Exception as e:
            logger.error(f"Failed to create FAISS index: {str(e)}")
            # 创建一个简单的备用索引
            self.index = faiss.IndexFlatIP(self.dimension) if self.metric == "inner_product" else faiss.IndexFlatL2(self.dimension)
            logger.info("Created fallback Flat index")
    
    def _load_index(self):
        """
        加载现有的 FAISS 索引和元数据
        """
        try:
            logger.info(f"Loading FAISS index from {self.index_path}")
            self.index = faiss.read_index(f"{self.index_path}.index")
            
            # 加载元数据
            metadata_path = f"{self.index_path}.meta.json"
            if os.path.exists(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    self.doc_ids = metadata.get("doc_ids", [])
                    self.doc_texts = metadata.get("doc_texts", [])
                    self.doc_metadata = metadata.get("doc_metadata", [])
                    self.dimension = metadata.get("dimension", self.dimension)
                    self.index_type = metadata.get("index_type", self.index_type)
                    self.metric = metadata.get("metric", self.metric)
            
            logger.info(f"Loaded index with {len(self.doc_ids)} documents")
            
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {str(e)}")
            # 创建一个新的索引
            self._create_index()
    
    def save(self, index_path: Optional[str] = None):
        """
        保存索引和元数据
        
        Args:
            index_path: 索引保存路径，如果为 None，则使用初始化时提供的路径
        """
        if index_path:
            self.index_path = index_path
        
        if not self.index_path:
            logger.warning("No index path provided, skipping save operation")
            return
        
        try:
            # 创建目录（如果不存在）
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            # 保存索引
            logger.info(f"Saving FAISS index to {self.index_path}")
            faiss.write_index(self.index, f"{self.index_path}.index")
            
            # 保存元数据
            metadata = {
                "doc_ids": self.doc_ids,
                "doc_texts": self.doc_texts,
                "doc_metadata": self.doc_metadata,
                "dimension": self.dimension,
                "index_type": self.index_type,
                "metric": self.metric
            }
            
            with open(f"{self.index_path}.meta.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved index with {len(self.doc_ids)} documents")
            
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {str(e)}")
    
    def add_documents(
        self, 
        embeddings: np.ndarray, 
        doc_ids: List[str], 
        doc_texts: List[str],
        doc_metadata: Optional[List[Dict[str, Any]]] = None
    ):
        """
        向索引添加文档
        
        Args:
            embeddings: 文档嵌入向量，形状为 (n, dimension)
            doc_ids: 文档ID列表
            doc_texts: 文档文本列表
            doc_metadata: 文档元数据列表
        """
        try:
            if len(embeddings) != len(doc_ids) or len(embeddings) != len(doc_texts):
                raise ValueError("Embeddings, doc_ids, and doc_texts must have the same length")
            
            # 确保元数据列表长度一致
            if doc_metadata is None:
                doc_metadata = [{} for _ in range(len(doc_ids))]
            elif len(doc_metadata) != len(doc_ids):
                raise ValueError("doc_metadata must have the same length as doc_ids")
            
            # 如果是IVF索引且尚未训练，则需要先训练
            if self.index_type == "IVF" and not self.index.is_trained:
                if len(embeddings) < 10:
                    logger.warning("Not enough embeddings for training IVF index. Using random vectors.")
                    # 创建随机向量进行训练
                    train_vectors = np.random.random((max(100, len(embeddings)), self.dimension)).astype(np.float32)
                    if self.metric == "inner_product":
                        # 对于内积度量，需要标准化向量
                        train_vectors = train_vectors / np.linalg.norm(train_vectors, axis=1, keepdims=True)
                else:
                    train_vectors = embeddings
                
                logger.info("Training IVF index...")
                self.index.train(train_vectors)
            
            # 确保向量类型正确
            embeddings = embeddings.astype(np.float32)
            
            # 为了保证向量索引与文档ID一致，从当前最大ID开始编号
            start_idx = len(self.doc_ids)
            
            # 添加到索引
            self.index.add(embeddings)
            
            # 更新文档信息
            self.doc_ids.extend(doc_ids)
            self.doc_texts.extend(doc_texts)
            self.doc_metadata.extend(doc_metadata)
            
            logger.info(f"Added {len(doc_ids)} documents to index. Total: {len(self.doc_ids)}")
            
        except Exception as e:
            logger.error(f"Failed to add documents to index: {str(e)}")
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 5, 
        include_texts: bool = True, 
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        根据查询嵌入搜索最相似的文档
        
        Args:
            query_embedding: 查询嵌入向量，形状为 (dimension,) 或 (1, dimension)
            top_k: 返回的文档数量
            include_texts: 是否包含文档文本
            include_metadata: 是否包含文档元数据
        
        Returns:
            搜索结果，包含相似度得分、文档ID、文档文本（可选）和元数据（可选）
        """
        try:
            # 确保查询向量形状正确
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)
            
            # 确保向量类型正确
            query_embedding = query_embedding.astype(np.float32)
            
            # 如果索引为空，返回空结果
            if len(self.doc_ids) == 0:
                return {
                    "scores": [],
                    "doc_ids": [],
                    "doc_texts": [] if include_texts else None,
                    "doc_metadata": [] if include_metadata else None
                }
            
            # 执行搜索
            k = min(top_k, len(self.doc_ids))
            scores, indices = self.index.search(query_embedding, k)
            
            # 提取结果
            result_doc_ids = [self.doc_ids[idx] for idx in indices[0] if 0 <= idx < len(self.doc_ids)]
            result_scores = scores[0].tolist()
            
            result = {
                "scores": result_scores,
                "doc_ids": result_doc_ids
            }
            
            # 添加文档文本
            if include_texts:
                result["doc_texts"] = [self.doc_texts[idx] for idx in indices[0] if 0 <= idx < len(self.doc_texts)]
            
            # 添加元数据
            if include_metadata:
                result["doc_metadata"] = [self.doc_metadata[idx] for idx in indices[0] if 0 <= idx < len(self.doc_metadata)]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to search in index: {str(e)}")
            # 返回空结果
            return {
                "scores": [],
                "doc_ids": [],
                "doc_texts": [] if include_texts else None,
                "doc_metadata": [] if include_metadata else None
            }
    
    def batch_search(
        self, 
        query_embeddings: np.ndarray, 
        top_k: int = 5, 
        include_texts: bool = True, 
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量搜索
        
        Args:
            query_embeddings: 查询嵌入向量，形状为 (n, dimension)
            top_k: 每个查询返回的文档数量
            include_texts: 是否包含文档文本
            include_metadata: 是否包含文档元数据
        
        Returns:
            每个查询的搜索结果列表
        """
        try:
            # 确保向量类型正确
            query_embeddings = query_embeddings.astype(np.float32)
            
            # 如果索引为空，返回空结果
            if len(self.doc_ids) == 0:
                return [{
                    "scores": [],
                    "doc_ids": [],
                    "doc_texts": [] if include_texts else None,
                    "doc_metadata": [] if include_metadata else None
                } for _ in range(len(query_embeddings))]
            
            # 执行搜索
            k = min(top_k, len(self.doc_ids))
            scores, indices = self.index.search(query_embeddings, k)
            
            # 处理结果
            results = []
            for i in range(len(query_embeddings)):
                result_indices = indices[i]
                result_doc_ids = [self.doc_ids[idx] for idx in result_indices if 0 <= idx < len(self.doc_ids)]
                result_scores = scores[i].tolist()
                
                result = {
                    "scores": result_scores,
                    "doc_ids": result_doc_ids
                }
                
                # 添加文档文本
                if include_texts:
                    result["doc_texts"] = [self.doc_texts[idx] for idx in result_indices if 0 <= idx < len(self.doc_texts)]
                
                # 添加元数据
                if include_metadata:
                    result["doc_metadata"] = [self.doc_metadata[idx] for idx in result_indices if 0 <= idx < len(self.doc_metadata)]
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform batch search: {str(e)}")
            # 返回空结果
            return [{
                "scores": [],
                "doc_ids": [],
                "doc_texts": [] if include_texts else None,
                "doc_metadata": [] if include_metadata else None
            } for _ in range(len(query_embeddings))]
    
    def delete(self, doc_ids: List[str]):
        """
        从索引中删除文档（注意：当前FAISS不直接支持删除，此处采用重建索引的方式）
        
        Args:
            doc_ids: 要删除的文档ID列表
        """
        try:
            # 检查索引是否存在
            if self.index is None or len(self.doc_ids) == 0:
                logger.warning("Index is empty, nothing to delete")
                return
            
            # 获取要删除的文档在当前索引中的位置
            delete_set = set(doc_ids)
            keep_indices = [i for i, doc_id in enumerate(self.doc_ids) if doc_id not in delete_set]
            
            # 如果没有文档要保留，则清空索引
            if len(keep_indices) == 0:
                logger.info("Deleting all documents from index")
                self._create_index()  # 重新创建空索引
                self.doc_ids = []
                self.doc_texts = []
                self.doc_metadata = []
                return
            
            # 如果删除后的文档数量与原数量相同，说明没有找到要删除的文档
            if len(keep_indices) == len(self.doc_ids):
                logger.warning("No documents found with the provided doc_ids")
                return
            
            logger.info(f"Rebuilding index after deleting {len(self.doc_ids) - len(keep_indices)} documents")
            
            # 由于FAISS不支持直接删除，我们需要重建索引
            # 1. 获取所有向量
            all_vectors = faiss.extract_index_vectors(self.index)[1].reshape(-1, self.dimension)
            
            # 2. 仅保留未删除的向量及其元数据
            keep_vectors = all_vectors[keep_indices]
            keep_doc_ids = [self.doc_ids[i] for i in keep_indices]
            keep_doc_texts = [self.doc_texts[i] for i in keep_indices]
            keep_doc_metadata = [self.doc_metadata[i] for i in keep_indices]
            
            # 3. 重新创建索引
            self._create_index()
            
            # 4. 将保留的向量和元数据添加到索引
            self.add_documents(keep_vectors, keep_doc_ids, keep_doc_texts, keep_doc_metadata)
            
            logger.info(f"Successfully deleted documents. Remaining: {len(self.doc_ids)}")
            
        except Exception as e:
            logger.error(f"Failed to delete documents from index: {str(e)}")
    
    def close(self):
        """
        关闭向量存储并释放资源
        """
        logger.info("Closing vector store")
        
        # 如果索引已经修改，保存更改
        if self.index_path:
            self.save()
        
        # 释放资源
        if hasattr(self, "index") and self.index is not None:
            del self.index 