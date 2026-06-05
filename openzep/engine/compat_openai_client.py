import json
import logging
import re
from typing import get_origin, get_args
from typing import Any

import openai
from pydantic import BaseModel

from graphiti_core.llm_client.config import DEFAULT_MAX_TOKENS, ModelSize
from graphiti_core.llm_client.errors import RateLimitError
from graphiti_core.llm_client.openai_generic_client import (
    DEFAULT_MODEL,
    OpenAIGenericClient,
)
from graphiti_core.prompts.models import Message

logger = logging.getLogger(__name__)


class CompatOpenAIGenericClient(OpenAIGenericClient):
    """OpenAI-compatible client with tolerant JSON extraction for loose proxies."""

    @staticmethod
    def _is_list_field(response_model: type[BaseModel], field_name: str) -> bool:
        field = response_model.model_fields[field_name]
        return get_origin(field.annotation) is list

    @staticmethod
    def _extract_json_text(raw: str) -> str:
        text = (raw or "").strip()
        if not text:
            return text

        if text.startswith("```"):
            lines = text.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
            if text.lower().startswith("json"):
                text = text[4:].lstrip()

        decoder = json.JSONDecoder()
        for idx, ch in enumerate(text):
            if ch not in "{[":
                continue
            try:
                obj, end = decoder.raw_decode(text[idx:])
                return json.dumps(obj, ensure_ascii=False)
            except json.JSONDecodeError:
                continue

        return text

    @staticmethod
    def _inner_model(
        response_model: type[BaseModel],
        list_field: str,
    ) -> type[BaseModel] | None:
        """Return the item model for a list field like `edges: list[Edge]`."""
        field_info = response_model.model_fields[list_field]
        origin = get_origin(field_info.annotation)
        if origin is list:
            args = get_args(field_info.annotation)
            if args and isinstance(args[0], type) and issubclass(args[0], BaseModel):
                return args[0]
        return None

    @staticmethod
    def _normalize_payload(
        payload: Any,
        response_model: type[BaseModel] | None,
        messages: list[Message],
    ) -> Any:
        if response_model is None:
            return payload

        field_names = list(response_model.model_fields.keys())

        # ── Named fallbacks for known graphiti-core models ──────────────────────
        # Run these BEFORE the generic fallback so the smarter field mapping
        # takes priority.

        if (
            response_model.__name__ == "ExtractedEntities"
            and isinstance(payload, dict)
            and isinstance(payload.get("extracted_entities"), list)
        ):
            type_map = CompatOpenAIGenericClient._extract_entity_type_map(messages)
            normalized_entities = []
            for item in payload["extracted_entities"]:
                if not isinstance(item, dict):
                    normalized_entities.append(item)
                    continue

                normalized = dict(item)
                if "name" not in normalized and "entity_name" in normalized:
                    normalized["name"] = normalized.pop("entity_name")

                if "entity_type_id" not in normalized and "entity_type_name" in normalized:
                    normalized["entity_type_id"] = type_map.get(str(normalized["entity_type_name"]), 0)

                if "entity_type_id" not in normalized:
                    normalized["entity_type_id"] = 0

                if "name" not in normalized:
                    normalized["name"] = normalized.get("entity_name", normalized.get("label", "Unknown"))

                normalized_entities.append(normalized)

            payload["extracted_entities"] = normalized_entities

        if (
            response_model.__name__ == "ExtractedEdges"
            and isinstance(payload, dict)
            and isinstance(payload.get("edges"), list)
        ):
            normalized_edges = []
            for item in payload["edges"]:
                if not isinstance(item, dict):
                    normalized_edges.append(item)
                    continue

                normalized = dict(item)
                if "source_entity_name" not in normalized:
                    normalized["source_entity_name"] = normalized.get(
                        "source_name", normalized.get("source", "Unknown"),
                    )
                if "target_entity_name" not in normalized:
                    normalized["target_entity_name"] = normalized.get(
                        "target_name", normalized.get("target", "Unknown"),
                    )
                if "relation_type" not in normalized:
                    normalized["relation_type"] = normalized.get(
                        "type", normalized.get("relationship", normalized.get("name", "RELATED_TO")),
                    )
                if "fact" not in normalized:
                    normalized["fact"] = normalized.get(
                        "description", normalized.get("summary", ""),
                    )
                if "episode_indices" not in normalized:
                    normalized["episode_indices"] = [0]

                normalized_edges.append(normalized)

            payload["edges"] = normalized_edges

        if (
            response_model.__name__ == "SummarizedEntities"
            and isinstance(payload, dict)
            and isinstance(payload.get("summaries"), list)
        ):
            safe_summaries = []
            for item in payload["summaries"]:
                if not isinstance(item, dict):
                    safe_summaries.append(item)
                    continue
                normalized = dict(item)
                if "name" not in normalized:
                    normalized["name"] = normalized.get("entity_name", "Unknown")
                if "summary" not in normalized:
                    normalized["summary"] = normalized.get("description", normalized.get("text", ""))
                safe_summaries.append(normalized)
            payload["summaries"] = safe_summaries

        # ── Single-field payload normalization ──────────────────────────────────
        if len(field_names) == 1:
            field_name = field_names[0]
            expects_list = CompatOpenAIGenericClient._is_list_field(response_model, field_name)

            if isinstance(payload, list):
                payload = {field_name: payload}
            elif expects_list and isinstance(payload, dict):
                if field_name not in payload:
                    payload = {field_name: [payload]}
                elif isinstance(payload[field_name], dict):
                    payload = {**payload, field_name: [payload[field_name]]}

        # ── Generic fallback: patch any missing required fields for
        #     models we don't have named logic for ────────────────────────────
        if len(field_names) == 1 and isinstance(payload, dict):
            list_field = field_names[0]
            items = payload.get(list_field)
            if isinstance(items, list):
                inner_model = CompatOpenAIGenericClient._inner_model(response_model, list_field)
                if inner_model is not None:
                    required = {
                        f_name
                        for f_name, f_info in inner_model.model_fields.items()
                        if f_info.is_required()
                    }
                    if required:
                        generic_defaults = {
                            int: 0,
                            float: 0.0,
                            str: "",
                            bool: False,
                            list: [],
                            dict: {},
                        }
                        safe_items: list[dict[str, Any]] = []
                        for item in items:
                            if not isinstance(item, dict):
                                safe_items.append(item)
                                continue
                            normalized = dict(item)
                            for f_name in required:
                                if f_name not in normalized:
                                    f_info = inner_model.model_fields[f_name]
                                    anno = f_info.annotation
                                    if anno is not None:
                                        normalized[f_name] = generic_defaults.get(
                                            anno, "",
                                        )
                            safe_items.append(normalized)
                        payload[list_field] = safe_items

        return payload

    @staticmethod
    def _extract_entity_type_map(messages: list[Message]) -> dict[str, int]:
        pattern = re.compile(r"<ENTITY TYPES>\s*(.*?)\s*</ENTITY TYPES>", re.DOTALL)
        for message in messages:
            match = pattern.search(message.content)
            if not match:
                continue
            block = match.group(1).strip()
            try:
                data = json.loads(block)
            except json.JSONDecodeError:
                continue

            mapping = {}
            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("entity_type_name")
                    entity_type_id = item.get("entity_type_id")
                    if isinstance(name, str) and isinstance(entity_type_id, int):
                        mapping[name] = entity_type_id
            return mapping

        return {}

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, Any]:
        openai_messages = []
        for message in messages:
            message.content = self._clean_input(message.content)
            if message.role in {"user", "system"}:
                openai_messages.append({"role": message.role, "content": message.content})

        try:
            # DeepSeek and some proxies don't support json_schema;
            # use json_object only when response_model is None (it's safer).
            # With a response_model, we skip response_format entirely —
            # graphiti's _extract_json_text will parse the raw output.
            response_kwargs: dict[str, Any] = {}
            if response_model is None:
                response_kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(
                model=self.model or DEFAULT_MODEL,
                messages=openai_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **response_kwargs,  # type: ignore[arg-type]
            )

            raw_content = response.choices[0].message.content or ""
            normalized = self._extract_json_text(raw_content)
            if not normalized:
                raise json.JSONDecodeError("Empty content", raw_content, 0)

            parsed = json.loads(normalized)
            result = self._normalize_payload(parsed, response_model, messages)

            # Debug: log what DeepSeek returned vs what we patched
            model_name = response_model.__name__ if response_model else "None"
            logger.info(
                "LLM parse OK model=%s raw_keys=%s result_keys=%s",
                model_name,
                list(parsed.keys()) if isinstance(parsed, dict) else type(parsed).__name__,
                list(result.keys()) if isinstance(result, dict) else type(result).__name__,
            )
            return result
        except json.JSONDecodeError:
            raise
        except openai.RateLimitError as exc:
            raise RateLimitError from exc
        except Exception as exc:
            logger.error("Error in generating LLM response: %s", exc)
            # Return a fallback empty response matching the expected model shape
            if response_model is not None:
                field_names = list(response_model.model_fields.keys())
                if len(field_names) == 1:
                    return {field_names[0]: []}
            raise
