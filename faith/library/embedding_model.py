import os
import torch
import logging
import numpy as np
from typing import List, Union, Dict, Any, Optional
from pathlib import Path

# 假设我们可以使用 SentenceTransformers 库进行嵌入
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class EmbeddingModel:
    """
    文本嵌入模型，用于将文本转换为向量表示
    """
    
    def __init__(
        self,
        model_name: str,
        model_path: Optional[str] = None,
        device: str = "cuda",
        normalize_embeddings: bool = True,
        **kwargs
    ):
        """
        初始化嵌入模型
        
        Args:
            model_name: 模型名称
            model_path: 模型路径，如果为 None，则从 model_name 加载
            device: 使用的设备（cuda 或 cpu）
            normalize_embeddings: 是否对嵌入向量进行归一化
            **kwargs: 其他参数
        """
        self.model_name = model_name
        self.model_path = model_path or model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings
        
        # 检查设备可用性
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA is not available, falling back to CPU")
            self.device = "cpu"
        
        # 加载模型
        self.model = self._load_model()
        
        logger.info(f"Embedding model {model_name} initialized on {self.device}")
    
    def _load_model(self) -> Any:
        """
        加载嵌入模型
        
        Returns:
            加载的模型
        """
        try:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError(
                    "sentence-transformers package is not installed. "
                    "Please install it with `pip install sentence-transformers`"
                )
            
            logger.info(f"Loading embedding model from {self.model_path}")
            model = SentenceTransformer(self.model_path, device=self.device)
            
            return model
        
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            # 创建一个简单的模拟模型进行替代（仅用于示例）
            return MockEmbeddingModel(self.model_name, self.device)
    
    def encode(
        self, 
        texts: Union[str, List[str]], 
        batch_size: int = 32, 
        show_progress_bar: bool = False,
        **kwargs
    ) -> np.ndarray:
        """
        将文本编码为向量
        
        Args:
            texts: 单个文本或文本列表
            batch_size: 批处理大小
            show_progress_bar: 是否显示进度条
            **kwargs: 传递给模型的其他参数
        
        Returns:
            文本的向量表示
        """
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            # 使用模型编码文本
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress_bar,
                convert_to_numpy=True,
                normalize_embeddings=self.normalize_embeddings,
                **kwargs
            )
            
            return embeddings
        
        except Exception as e:
            logger.error(f"Failed to encode texts: {str(e)}")
            # 返回零向量作为替代
            return np.zeros((len(texts), 768), dtype=np.float32)
    
    def encode_queries(self, queries: Union[str, List[str]], **kwargs) -> np.ndarray:
        """
        编码查询文本，可以应用特定于查询的处理
        
        Args:
            queries: 单个查询或查询列表
            **kwargs: 其他参数
        
        Returns:
            查询的向量表示
        """
        return self.encode(queries, **kwargs)
    
    def encode_documents(self, documents: Union[str, List[str]], **kwargs) -> np.ndarray:
        """
        编码文档文本，可以应用特定于文档的处理
        
        Args:
            documents: 单个文档或文档列表
            **kwargs: 其他参数
        
        Returns:
            文档的向量表示
        """
        return self.encode(documents, **kwargs)
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        计算两个嵌入向量之间的相似度
        
        Args:
            embedding1: 第一个嵌入向量
            embedding2: 第二个嵌入向量
        
        Returns:
            两个向量之间的余弦相似度
        """
        if embedding1.ndim == 1:
            embedding1 = embedding1.reshape(1, -1)
        if embedding2.ndim == 1:
            embedding2 = embedding2.reshape(1, -1)
        
        # 如果向量未归一化，进行归一化
        if not self.normalize_embeddings:
            embedding1 = embedding1 / np.linalg.norm(embedding1, axis=1, keepdims=True)
            embedding2 = embedding2 / np.linalg.norm(embedding2, axis=1, keepdims=True)
        
        # 计算余弦相似度
        return np.dot(embedding1, embedding2.T)[0, 0]
    
    def close(self):
        """
        释放资源
        """
        logger.info(f"Closing embedding model {self.model_name}")
        
        # 释放模型资源
        if hasattr(self, "model") and self.model is not None:
            # 删除模型以释放内存
            del self.model
            
            # 清理 CUDA 缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


class MockEmbeddingModel:
    """
    模拟嵌入模型，用于在无法加载实际模型时提供替代功能
    """
    
    def __init__(self, model_name: str, device: str):
        """
        初始化模拟模型
        
        Args:
            model_name: 模型名称
            device: 使用的设备
        """
        self.model_name = model_name
        self.device = device
        self.embedding_dim = 768  # 模拟的嵌入维度
        
        logger.warning(f"Using mock embedding model for {model_name}")
    
    def encode(
        self, 
        texts: List[str], 
        batch_size: int = 32, 
        show_progress_bar: bool = False,
        convert_to_numpy: bool = True,
        normalize_embeddings: bool = True,
        **kwargs
    ) -> np.ndarray:
        """
        模拟编码文本
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
            show_progress_bar: 是否显示进度条
            convert_to_numpy: 是否转换为 NumPy 数组
            normalize_embeddings: 是否归一化嵌入向量
            **kwargs: 其他参数
        
        Returns:
            模拟的文本向量表示
        """
        # 为每个文本生成一个唯一的伪随机向量
        embeddings = np.array([
            np.frombuffer(text.encode(), dtype=np.uint8).astype(np.float32)[:self.embedding_dim] 
            if len(text.encode()) >= self.embedding_dim
            else np.pad(
                np.frombuffer(text.encode(), dtype=np.uint8).astype(np.float32),
                (0, self.embedding_dim - len(text.encode())),
                mode='constant'
            )
            for text in texts
        ])
        
        # 补齐维度
        if embeddings.shape[1] < self.embedding_dim:
            embeddings = np.pad(
                embeddings,
                ((0, 0), (0, self.embedding_dim - embeddings.shape[1])),
                mode='constant'
            )
        
        # 截断维度
        embeddings = embeddings[:, :self.embedding_dim]
        
        # 归一化
        if normalize_embeddings:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / norms
        
        return embeddings 