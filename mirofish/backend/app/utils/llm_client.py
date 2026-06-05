"""
LLM客户端封装
统一使用OpenAI格式调用
"""

import json
import re
import time
from typing import Optional, Dict, Any, List
from openai import OpenAI

from ..config import Config


class LLMClient:
    """LLM客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        request_timeout: int = 120,
        max_retries: int = 3,
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME
        self.request_timeout = request_timeout
        self.max_retries = max_retries

        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=request_timeout,
            max_retries=0,  # 我们自己控制重试
        )

    def _call_with_retry(
        self,
        kwargs: Dict[str, Any],
        operation_name: str = "LLM call",
    ) -> str:
        """带指数退避重试的 LLM 调用"""
        last_exception = None
        delay = 2.0

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                # 部分模型（如MiniMax M2.5）会在content中包含<think>思考内容，需要移除
                content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
                return content
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"{operation_name} 第 {attempt + 1} 次尝试失败: {str(e)[:200]}, "
                        f"{delay:.1f}秒后重试..."
                    )
                    time.sleep(delay)
                    delay *= 2  # 指数退避: 2s, 4s, 8s
                else:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"{operation_name} 在 {self.max_retries} 次尝试后仍失败: {str(e)}")

        raise last_exception

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（如JSON模式）

        Returns:
            模型响应文本
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        return self._call_with_retry(kwargs, "LLM chat")
    
    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        发送聊天请求并返回JSON
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            解析后的JSON对象
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        # 清理markdown代码块标记
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"LLM返回的JSON格式无效: {cleaned_response}")

