"""
app.services.llm — LLM integration layer.

Supports OpenAI-compatible and Google Gemini providers.
Preserves the original ChatAgent + rule-based fallback pattern.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class LLMParams:
    api_key: str = ""
    base_url: str = ""
    model: str = "gpt-4o-mini"
    provider: str = "openai"


SYSTEM_PROMPT = (
    "你是一位慢性病管理 AI 助手 (CarePilot)，专注于中国大陆 2 型糖尿病合并高血压患者的日常健康管理。"
    "请从以下五个维度给出简洁、专业且友好的建议：控糖、控压、依从性、饮食和复诊准备。"
    "回复必须使用简体中文，并在必要时引用患者的最新监测数据来佐证你的分析。"
    "如果信息不足，主动引导患者补充今日血糖、血压、饮食或服药情况。"
)


def _build_llm_params_from_settings() -> LLMParams:
    """Build LLMParams from app settings."""
    s = get_settings()
    return LLMParams(
        api_key=s.llm_api_key,
        base_url=s.llm_base_url,
        model=s.llm_model,
        provider=s.llm_provider,
    )


class ChatAgent:
    """Wraps both real LLM calls and a rule-based fallback."""

    def reply(
        self,
        user_message: str,
        recent_messages: Sequence[tuple[str, str]],
        extra_context: str = "",
        llm_params: Optional[LLMParams] = None,
    ) -> str:
        params = llm_params or _build_llm_params_from_settings()
        settings = get_settings()

        use_real = bool(params.api_key and not settings.enable_fake_llm)

        if use_real:
            try:
                if params.provider == "google":
                    return self._google_llm_call(user_message, recent_messages, extra_context, params)
                return self._openai_llm_call(user_message, recent_messages, extra_context, params)
            except Exception as exc:
                logger.warning("LLM call failed, falling back to rules: %s", exc)
                return f"[LLM 调用失败: {exc}]\n\n" + self._fake_reply(user_message, recent_messages, extra_context)

        return self._fake_reply(user_message, recent_messages, extra_context)

    # ── OpenAI-Compatible Call ────────────────────────────
    def _openai_llm_call(
        self, user_message: str, recent_messages: Sequence[tuple[str, str]],
        extra_context: str, params: LLMParams,
    ) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for role, content in recent_messages[-6:]:
            messages.append({"role": role, "content": content})
        if extra_context:
            messages.append({
                "role": "system",
                "content": f"以下是患者的当前健康概览，请结合此信息回复：{extra_context}",
            })
        messages.append({"role": "user", "content": user_message})

        base = (params.base_url or "https://api.openai.com").rstrip("/")
        if not base.endswith("/v1") and not base.endswith("/chat/completions"):
            url = f"{base}/v1/chat/completions"
        elif base.endswith("/v1"):
            url = f"{base}/chat/completions"
        else:
            url = base

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {params.api_key}",
        }
        payload = {
            "model": params.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"].strip()

    # ── Google Gemini Call ────────────────────────────────
    def _google_llm_call(
        self, user_message: str, recent_messages: Sequence[tuple[str, str]],
        extra_context: str, params: LLMParams,
    ) -> str:
        try:
            import google.generativeai as genai
        except ImportError:
            return "[Google Gemini SDK 未安装。请在 requirements.txt 中添加 google-generativeai]"

        genai.configure(api_key=params.api_key)
        model = genai.GenerativeModel(params.model or "gemini-1.5-flash")

        history_text = "\n".join(
            f"{'用户' if r == 'user' else '助手'}: {c}" for r, c in recent_messages[-6:]
        )
        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n历史对话:\n{history_text}\n\n"
            f"健康背景: {extra_context}\n\n用户: {user_message}"
        )
        response = model.generate_content(full_prompt)
        return response.text.strip()

    # ── Rule-Based Fallback ──────────────────────────────
    def _fake_reply(
        self, user_message: str, recent_messages: Sequence[tuple[str, str]],
        extra_context: str = "",
    ) -> str:
        prefix = "我会从控糖、控压、依从性、饮食和复诊准备角度给你建议。"
        if "总结" in user_message or "复诊" in user_message:
            return f"{prefix}\n你已经接近需要门诊摘要的场景，建议生成 previsit digest，并重点核对最近 7 到 14 天的血糖、血压、漏药和高风险饮食。\n{extra_context}".strip()
        if "血糖" in user_message:
            return f"{prefix}\n血糖管理重点是区分空腹和餐后模式，并结合晚餐结构、夜间加餐和漏服降糖药来判断。\n{extra_context}".strip()
        if "血压" in user_message:
            return f"{prefix}\n血压管理请优先关注晨间血压、盐摄入、睡眠不足和是否规律服用降压药。\n{extra_context}".strip()
        if any(k in user_message for k in ["吃", "饮食", "奶茶", "火锅", "外卖"]):
            return f"{prefix}\n饮食管理建议优先减少高糖饮料、主食过量和高盐外卖，并尽量把餐次记录得更具体。\n{extra_context}".strip()
        if "药" in user_message or "提醒" in user_message:
            return f"{prefix}\n请结合今日提醒和服药计划，核对是否存在漏服、错时服药或连续跳过的情况。\n{extra_context}".strip()
        if recent_messages:
            return f"{prefix}\n我已结合你最近的记录继续跟进。当前更建议补齐今天的血糖、血压、饮食或服药执行情况。\n{extra_context}".strip()
        return f"{prefix}\n你可以直接提问，也可以用 [TRACK] 记录血糖、血压、饮食、症状或体重。\n{extra_context}".strip()


# ── Planner (LLM-based intent detection) ─────────────────

PLANNER_SYSTEM_PROMPT = """你是一个专业的慢性病管理助手，能够理解用户意图并选择合适的工具来处理。
你面前有以下工具：
{tools_metadata}

请根据用户的输入，判断是否需要调用工具。
如果需要，请按以下JSON格式返回：
{{
  "thought": "你的思考过程",
  "name": "工具名称",
  "parameters": {{ "参数名": "参数值" }}
}}
如果不需要调用工具（即用户只是在闲聊或打招呼），请返回：
{{
  "thought": "这是一个普通对话",
  "name": null,
  "parameters": {{}}
}}
请只返回 JSON。
"""


class Planner:
    def plan(
        self, user_message: str, tools_metadata: list[dict],
        llm_params: Optional[LLMParams] = None,
    ) -> dict:
        params = llm_params or _build_llm_params_from_settings()
        settings = get_settings()
        use_real = bool(params.api_key and not settings.enable_fake_llm)

        if use_real:
            try:
                return self._real_llm_plan(user_message, tools_metadata, params)
            except Exception as exc:
                logger.warning(f"LLM planning failed: {exc}")
                return self._rule_based_plan(user_message)
        return self._rule_based_plan(user_message)

    def _real_llm_plan(self, user_message: str, tools_metadata: list[dict], params: LLMParams) -> dict:
        prompt = PLANNER_SYSTEM_PROMPT.format(
            tools_metadata=json.dumps(tools_metadata, ensure_ascii=False, indent=2)
        )
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message},
        ]

        base = (params.base_url or "https://api.openai.com").rstrip("/")
        if not base.endswith("/v1") and not base.endswith("/chat/completions"):
            url = f"{base}/v1/chat/completions"
        elif base.endswith("/v1"):
            url = f"{base}/chat/completions"
        else:
            url = base

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {params.api_key}",
        }
        payload = {
            "model": params.model,
            "messages": messages,
            "temperature": 0.1,
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "{" in content:
            content = content[content.find("{"):content.rfind("}") + 1]

        return json.loads(content)

    def _rule_based_plan(self, user_message: str) -> dict:
        msg = user_message.lower()
        if any(k in msg for k in ["总结", "概览", "情况", "最近怎么样"]):
            return {"thought": "用户询问健康概览", "name": "get_today_overview", "parameters": {}}
        if any(k in msg for k in ["记录", "记录了", "血压", "血糖", "体重"]):
            return {"thought": "用户录入健康数据", "name": "record_health_event", "parameters": {"raw_text": user_message}}
        if any(k in msg for k in ["药", "服药", "添加药物"]):
            if "添加" in msg or "加" in msg:
                return {"thought": "用户想要添加药物", "name": None, "parameters": {}}
            return {"thought": "用户询问药物清单", "name": "list_medications", "parameters": {}}
        if any(k in msg for k in ["吃了", "吃晚饭", "饮食", "中午吃"]):
            return {"thought": "用户正在描述饮食", "name": "analyze_meal", "parameters": {"description": user_message}}
        if "时间线" in msg or "历史" in msg:
            return {"thought": "用户查看时间线", "name": "get_timeline", "parameters": {}}
        return {"thought": "简单闲聊", "name": None, "parameters": {}}


class Executor:
    def __init__(self, tool_registry):
        self.tool_registry = tool_registry

    def execute(self, plan: dict) -> dict:
        tool_name = plan.get("name")
        params = plan.get("parameters", {})

        if not tool_name:
            return {"status": "skipped", "result": "无具体工具被选取。"}

        try:
            result = self.tool_registry.call_tool(tool_name, **params)
            return {
                "status": "success",
                "tool_name": tool_name,
                "parameters": params,
                "result": result,
            }
        except Exception as exc:
            logger.error(f"Execution Error: {exc}")
            return {
                "status": "error",
                "tool_name": tool_name,
                "error": str(exc),
                "result": f"执行器抛出异常：{exc}",
            }


class Orchestrator:
    """Top-level orchestrator: Plan → Execute → Respond."""

    def __init__(self, db, patient_id: int):
        from app.services.tools import ToolRegistry

        self.db = db
        self.patient_id = patient_id
        self.tool_registry = ToolRegistry(db, patient_id)
        self.planner = Planner()
        self.executor = Executor(self.tool_registry)
        self.chat_agent = ChatAgent()

    def handle_message(
        self, user_message: str,
        recent_messages: list[tuple[str, str]],
        llm_params: Optional[LLMParams] = None,
    ) -> dict:
        params = llm_params or _build_llm_params_from_settings()
        trace = []

        try:
            plan = self.planner.plan(user_message, self.tool_registry.get_tool_metadata(), params)
            trace.append({"step": "plan", "output": plan})

            execution_result = {}
            if plan.get("name"):
                execution_result = self.executor.execute(plan)
                trace.append({"step": "execute", "output": execution_result})

            tool_feedback = ""
            if execution_result.get("status") == "success":
                tool_feedback = f"【系统动作】已调用并成功执行工具：{execution_result.get('tool_name')}。结果已同步到当前会话。"
            elif execution_result.get("status") == "error":
                tool_feedback = f"【系统动作】试图执行工具 {execution_result.get('tool_name')} 时遇到问题，但仍将为您提供建议。"

            final_reply = self.chat_agent.reply(
                user_message=user_message,
                recent_messages=recent_messages,
                extra_context=tool_feedback,
                llm_params=params,
            )

            return {
                "reply": final_reply,
                "trace": trace,
                "has_tool_use": bool(plan.get("name")),
                "status": "success",
            }
        except Exception as exc:
            logger.error(f"Orchestrator Error: {exc}", exc_info=True)
            return {
                "reply": f"抱歉，系统在处理您的请求时遇到了内部错误。请复查您的模型配置或稍后重试。\n错误详情: {exc}",
                "trace": trace,
                "has_tool_use": False,
                "status": "error",
            }
