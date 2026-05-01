"""
Tutor Agent (RAG) for document-based learning with curriculum, study plan, and enrollment.
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    ModelResponse,
    TextPart,
    ModelRequest,
    UserPromptPart,
    SystemPromptPart,
)

from configs.config import config
from model import select_model
from models.states import TutorResponse
from models.tutor_models import UserEnrollment
from service.document_processor import get_document_processor
from service.database import get_database_service
from utils import (
    process_chat_history_for_model_inference,
    save_chat_history_to_storage,
    get_chat_history_from_storage,
)

logger = logging.getLogger(__name__)


@dataclass
class UserDependencies:
    """Runtime context for the tutor agent."""

    user_id: str
    document_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    enrollment_id: Optional[str] = None
    profession: Optional[str] = None
    subject_of_study: Optional[str] = None
    filenames: Optional[List[str]] = None
    user_enrollment: Optional[UserEnrollment] = None
    current_lesson_id: Optional[str] = None
    user_performance_analysis: Optional[Dict[str, Any]] = None


class TutorAgent:
    """Tutor with RAG, curriculum tools, and enrollment-scoped sessions."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        provider: str = "google",
    ):
        self._model_name = model_name
        self._api_key = api_key
        self._provider = provider
        self.system_prompt = self._build_system_prompt()
        model, _ = select_model(
            self._model_name or getattr(config, "TUTOR_MODEL_NAME", None) or "gemini-2.0-flash-exp",
            self._api_key or config.GOOGLE_API_KEY or "",
        )
        self.agent = Agent(
            model,
            deps_type=UserDependencies,
            system_prompt=self.system_prompt,
            output_type=Union[TutorResponse, str],
        )
        self.doc_processor = get_document_processor()
        self.db_service = get_database_service()
        self._register_tools()

    def _reinitialize_model(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """Rebuild the underlying model and re-register tools (e.g. after config change)."""
        if model_name is not None:
            self._model_name = model_name
        if api_key is not None:
            self._api_key = api_key
        model, _ = select_model(
            self._model_name or getattr(config, "TUTOR_MODEL_NAME", None) or "gemini-2.0-flash-exp",
            self._api_key or config.GOOGLE_API_KEY or "",
        )
        self.agent = Agent(
            model,
            deps_type=UserDependencies,
            system_prompt=self.system_prompt,
            output_type=Union[TutorResponse, str],
        )
        self._register_tools()

    def _format_dynamic_context_block(
        self,
        *,
        current_lesson_title: Optional[str] = None,
        lesson_objectives: Optional[List[str]] = None,
        lesson_content_preview: Optional[str] = None,
        performance_notes: Optional[str] = None,
    ) -> str:
        lines = ["### Current session data (inject into reasoning; do not repeat verbatim unless helpful)"]
        if current_lesson_title:
            lines.append(f"- **Lesson focus:** {current_lesson_title}")
        if lesson_objectives:
            lines.append("- **Objectives:**")
            for o in lesson_objectives:
                lines.append(f"  - {o}")
        if lesson_content_preview:
            preview = lesson_content_preview.strip()
            if len(preview) > 2000:
                preview = preview[:2000] + "…"
            lines.append("- **Relevant material (excerpt from document):**")
            lines.append(preview)
        if performance_notes:
            lines.append(f"- **Progress / notes:** {performance_notes}")
        if len(lines) == 1:
            return ""
        return "\n".join(lines)

    def add_data(
        self,
        chat_history: Optional[List[Union[ModelRequest, ModelResponse]]] = None,
        *,
        current_lesson_title: Optional[str] = None,
        lesson_objectives: Optional[List[str]] = None,
        lesson_content_preview: Optional[str] = None,
        performance_notes: Optional[str] = None,
    ) -> List[Union[ModelRequest, ModelResponse]]:
        """
        Merge lesson objectives, document excerpts, and performance notes into the
        system prompt carried by chat history. If history is empty, seeds from
        `self.system_prompt` plus the dynamic block.
        """
        dynamic = self._format_dynamic_context_block(
            current_lesson_title=current_lesson_title,
            lesson_objectives=lesson_objectives,
            lesson_content_preview=lesson_content_preview,
            performance_notes=performance_notes,
        )
        base = self.system_prompt
        if dynamic:
            full_system = f"{base}\n\n{dynamic}"
        else:
            full_system = base

        hist = list(chat_history or [])
        if not hist:
            return [ModelRequest(parts=[SystemPromptPart(content=full_system)])]

        for i, msg in enumerate(hist):
            if not isinstance(msg, ModelRequest):
                continue
            for j, part in enumerate(msg.parts):
                if isinstance(part, SystemPromptPart):
                    new_parts = list(msg.parts)
                    new_parts[j] = SystemPromptPart(content=full_system)
                    hist[i] = ModelRequest(parts=new_parts)
                    return hist

        hist.insert(0, ModelRequest(parts=[SystemPromptPart(content=full_system)]))
        return hist

    async def _resolve_lesson_context(
        self, user_id: str, document_id: Optional[str]
    ) -> Dict[str, Any]:
        """Load next lesson + module objectives and a short RAG preview for add_data()."""
        out: Dict[str, Any] = {}
        if not document_id:
            return out
        en = await self.db_service.get_enrollment_by_user_document(str(user_id), str(document_id))
        if not en:
            return out
        sp = await self.db_service.get_study_plan(en["study_plan_id"])
        cur = await self.db_service.get_curriculum(en["curriculum_id"])
        if not sp or not cur:
            return out
        raw = sp.get("daily_schedule") or []
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = []
        next_task = None
        for t in raw:
            if not t.get("is_completed"):
                next_task = t
                break
        if not next_task:
            out["performance_notes"] = (
                "All scheduled lessons in this study plan are marked complete."
            )
            return out
        modules = cur.get("modules") or []
        if isinstance(modules, str):
            try:
                modules = json.loads(modules)
            except Exception:
                modules = []
        mid = next_task.get("module_id")
        title = next_task.get("title") or "Current lesson"
        objectives: List[str] = []
        for m in modules:
            if str(m.get("module_id")) == str(mid):
                o = m.get("objectives") or []
                if isinstance(o, str):
                    objectives = [o]
                else:
                    objectives = list(o)
                title = m.get("title") or title
                break
        out["current_lesson_title"] = title
        out["lesson_objectives"] = objectives
        query_bits = [title] + (objectives[:2] if objectives else [])
        q = " ".join(query_bits)[:500]
        try:
            results = await self.doc_processor.search_documents(
                query=q, document_id=str(document_id), top_k=2
            )
            preview = "\n\n".join(
                (r.get("content") or "")[:600] for r in results[:2]
            )
            if preview.strip():
                out["lesson_content_preview"] = preview.strip()
        except Exception as e:
            logger.debug("lesson RAG preview: %s", e)
        return out

    def _build_system_prompt(self) -> str:
        return """
You are an AI clinical tutor. You operate inside a single learning enrollment (document + curriculum + study plan).

Follow these steps on every turn:

1) **Context**
   - Read `UserDependencies` mentally: user_id, document_id, enrollment (if any), profession, subject_of_study, filenames.
   - If the user asks about the material, call `retrieve` with a focused search_query derived from their question.

2) **Curriculum & plan**
   - If the learner is starting a new topic or document and no curriculum exists yet, call `create_or_load_curriculum` with document_id (and subject if no document).
   - If they need a schedule, call `create_or_load_study_plan` with the curriculum_id returned earlier.
   - If they need formal enrollment linking user + curriculum + plan + document, call `create_or_load_enrollment`.

3) **Daily lesson**
   - When the user asks what to study next or wants to progress, call `get_next_lesson` to fetch the next incomplete daily task.

4) **Teaching**
   - Answer clearly, cite retrieved chunks when used.
   - Adapt difficulty to the learner; be concise.
   - If retrieval is empty, say so briefly and answer from general medical knowledge when appropriate.

5) **Quiz / Mediquest**
   - If the user wants a quiz on this material, set `generate_quiz=True` in your TutorResponse.
   - If they want to play Mediquest, set `play_quest=True`.

6) **Output**
   - Always respond with structured TutorResponse (response, sources, generate_quiz, play_quest) when possible.
   - Never fabricate citations; list sources only from retrieved content.

Tools: retrieve, create_or_load_curriculum, create_or_load_study_plan, create_or_load_enrollment, get_next_lesson, mark_task_completed.
"""

    def _register_tools(self) -> None:
        db = self.db_service
        dp = self.doc_processor

        @self.agent.tool
        async def retrieve(
            ctx: RunContext[UserDependencies],
            search_query: str,
            document_id: Optional[str] = None,
            top_k: int = 5,
        ) -> str:
            doc_id = document_id or ctx.deps.document_id
            if not doc_id:
                return "No document specified for retrieval."
            try:
                results = await dp.search_documents(
                    query=search_query, document_id=str(doc_id), top_k=top_k
                )
                parts = [
                    f"File: {r.get('file_name', 'Unknown')}\n"
                    f"Chunk [{r.get('chunk_index', 0)}] (score {r.get('score', 0):.2f}):\n"
                    f"{r.get('content', '')}"
                    for r in results
                ]
                return "\n\n".join(parts) if parts else "No relevant content found."
            except Exception as e:
                logger.error("retrieve: %s", e)
                return f"Error retrieving documents: {e}"

        @self.agent.tool
        async def create_or_load_curriculum(
            ctx: RunContext[UserDependencies],
            document_id: Optional[str] = None,
            subject: Optional[str] = None,
        ) -> str:
            uid = str(ctx.deps.user_id)
            doc_id = document_id or ctx.deps.document_id
            if not doc_id:
                return "document_id is required to create or load a curriculum."
            existing = db.get_curriculum_by_user_document(uid, str(doc_id))
            if existing:
                return json.dumps(
                    {"status": "ok", "curriculum_id": existing["id"], "title": existing.get("title")}
                )
            doc = db.get_document(str(doc_id))
            title = (doc or {}).get("name") or (doc or {}).get("file_name") or "Study material"
            preview = ((doc or {}).get("content") or "")[:800]
            subj = subject or ctx.deps.subject_of_study or ctx.deps.profession or "General medicine"
            modules = [
                {
                    "module_id": str(uuid.uuid4()),
                    "title": "Orientation",
                    "objectives": [f"Understand the scope of {title}", "Identify key themes"],
                    "content_ids": [],
                    "estimated_minutes": 45,
                    "is_completed": False,
                },
                {
                    "module_id": str(uuid.uuid4()),
                    "title": "Core concepts",
                    "objectives": ["Explain main mechanisms from the material", "Apply to simple cases"],
                    "content_ids": [],
                    "estimated_minutes": 60,
                    "is_completed": False,
                },
            ]
            row = db.upsert_curriculum(
                user_id=uid,
                document_id=str(doc_id),
                title=f"{title}",
                description=(preview[:200] + "…") if preview else f"Curriculum for {subj}",
                difficulty_level="Intermediate",
                modules=modules,
            )
            return json.dumps(
                {"status": "created", "curriculum_id": row.get("id"), "title": row.get("title")}
            )

        @self.agent.tool
        async def create_or_load_study_plan(
            ctx: RunContext[UserDependencies],
            curriculum_id: str,
        ) -> str:
            uid = str(ctx.deps.user_id)
            existing = db.get_study_plan_by_user_curriculum(uid, curriculum_id)
            if existing:
                return json.dumps({"status": "ok", "study_plan_id": existing["id"]})
            cur_row = db.get_curriculum(curriculum_id)
            if not cur_row:
                return "Curriculum not found."
            modules = cur_row.get("modules") or []
            if isinstance(modules, str):
                try:
                    modules = json.loads(modules)
                except Exception:
                    modules = []
            start = date.today()
            target = start + timedelta(days=max(7, len(modules) * 2))
            schedule: List[Dict[str, Any]] = []
            for i, m in enumerate(modules):
                mid = m.get("module_id") or str(uuid.uuid4())
                day = start + timedelta(days=i)
                schedule.append(
                    {
                        "task_id": str(uuid.uuid4()),
                        "module_id": mid,
                        "title": m.get("title", f"Module {i+1}"),
                        "is_completed": False,
                        "scheduled_date": day.isoformat(),
                        "actual_completion_date": None,
                    }
                )
            if not schedule:
                schedule = [
                    {
                        "task_id": str(uuid.uuid4()),
                        "module_id": str(uuid.uuid4()),
                        "title": "Day 1 study block",
                        "is_completed": False,
                        "scheduled_date": start.isoformat(),
                        "actual_completion_date": None,
                    }
                ]
            row = db.create_study_plan_row(
                user_id=uid,
                curriculum_id=curriculum_id,
                start_date=start.isoformat(),
                target_end_date=target.isoformat(),
                daily_schedule=schedule,
                pace_preference="balanced",
                progress=0.0,
            )
            return json.dumps({"status": "created", "study_plan_id": row.get("id")})

        @self.agent.tool
        async def create_or_load_enrollment(
            ctx: RunContext[UserDependencies],
            curriculum_id: str,
            study_plan_id: str,
        ) -> str:
            uid = str(ctx.deps.user_id)
            doc_id = ctx.deps.document_id
            if not doc_id:
                return "document_id is required to create enrollment."
            ex = db.get_enrollment_by_user_document(uid, str(doc_id))
            if ex:
                return json.dumps({"status": "ok", "enrollment_id": ex["id"]})
            row = db.create_user_enrollment_row(
                user_id=uid,
                curriculum_id=curriculum_id,
                study_plan_id=study_plan_id,
                document_id=str(doc_id),
            )
            return json.dumps({"status": "created", "enrollment_id": row.get("id")})

        @self.agent.tool
        async def get_next_lesson(ctx: RunContext[UserDependencies]) -> str:
            uid = str(ctx.deps.user_id)
            doc_id = ctx.deps.document_id
            if not doc_id:
                return "No document in context; cannot load next lesson."
            en = db.get_enrollment_by_user_document(uid, str(doc_id))
            if not en:
                return "No enrollment found for this document. Create curriculum, study plan, and enrollment first."
            sp = db.get_study_plan(en["study_plan_id"])
            if not sp:
                return "Study plan missing."
            raw = sp.get("daily_schedule") or []
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except Exception:
                    raw = []
            for t in raw:
                if not t.get("is_completed"):
                    return json.dumps(
                        {
                            "task_id": t.get("task_id"),
                            "title": t.get("title"),
                            "scheduled_date": t.get("scheduled_date"),
                            "module_id": t.get("module_id"),
                        }
                    )
            return "All scheduled tasks are marked complete. Great work."

        @self.agent.tool
        async def mark_task_completed(
            ctx: RunContext[UserDependencies],
            task_id: str,
        ) -> str:
            """Mark a daily-schedule task as completed and update progress."""
            uid = str(ctx.deps.user_id)
            doc_id = ctx.deps.document_id
            if not doc_id:
                return "No document in context."
            en = db.get_enrollment_by_user_document(uid, str(doc_id))
            if not en:
                return "No enrollment found for this document."
            ok = db.mark_study_plan_task_completed(en["study_plan_id"], task_id)
            if ok:
                return json.dumps({"status": "completed", "task_id": task_id})
            return "Task not found in study plan schedule."

    def _enrollment_from_row(self, row: Dict[str, Any]) -> UserEnrollment:
        return UserEnrollment(
            id=str(row["id"]),
            user_id=str(row["user_id"]),
            curriculum_id=str(row["curriculum_id"]),
            study_plan_id=str(row["study_plan_id"]),
            document_id=str(row["document_id"]),
            last_accessed=row.get("last_accessed") or datetime.utcnow(),
        )

    async def chat(
        self,
        user_id: str,
        user_message: str,
        document_id: Optional[str] = None,
        session_id: Optional[str] = None,
        chat_history: Optional[List[Union[ModelRequest, ModelResponse]]] = None,
        profession: Optional[str] = None,
        subject_of_study: Optional[str] = None,
        filenames: Optional[List[str]] = None,
        enrollment_id: Optional[str] = None,
        user_performance_analysis: Optional[Dict[str, Any]] = None,
    ) -> dict:
        enrollment: Optional[UserEnrollment] = None
        if enrollment_id:
            row = await self.db_service.get_user_enrollment(enrollment_id)
            if row and str(row.get("user_id")) == str(user_id):
                enrollment = self._enrollment_from_row(row)
                document_id = str(row.get("document_id"))
                await self.db_service.touch_enrollment(enrollment_id)

        conversation_id = session_id or enrollment_id or document_id or f"tutor-{user_id}"
        if chat_history is None:
            chat_history = await get_chat_history_from_storage(
                user_id=user_id,
                conversation_id=conversation_id,
                chat_type="tutor",
                document_id=document_id,
            )

        lesson_ctx = await self._resolve_lesson_context(user_id, document_id)
        perf_note = None
        if user_performance_analysis:
            try:
                perf_note = json.dumps(user_performance_analysis, default=str)[:1500]
            except Exception:
                perf_note = str(user_performance_analysis)[:1500]
        if perf_note:
            lesson_ctx["performance_notes"] = (
                (lesson_ctx.get("performance_notes") or "") + "\n" + perf_note
            ).strip()

        processed_history = (
            process_chat_history_for_model_inference(chat_history) if chat_history else []
        )
        processed_history = self.add_data(
            processed_history,
            current_lesson_title=lesson_ctx.get("current_lesson_title"),
            lesson_objectives=lesson_ctx.get("lesson_objectives"),
            lesson_content_preview=lesson_ctx.get("lesson_content_preview"),
            performance_notes=lesson_ctx.get("performance_notes"),
        )

        deps = UserDependencies(
            user_id=str(user_id),
            document_id=document_id,
            document_ids=[document_id] if document_id else None,
            enrollment_id=enrollment_id,
            profession=profession,
            subject_of_study=subject_of_study,
            filenames=filenames or [],
            user_enrollment=enrollment,
            user_performance_analysis=user_performance_analysis,
        )

        try:
            result = await self.agent.run(
                user_message, deps=deps, message_history=processed_history
            )
            out = result.output if hasattr(result, "output") else result
            if isinstance(out, TutorResponse):
                answer = out.response
                sources = out.sources or []
                generate_quiz = out.generate_quiz
                play_quest = out.play_quest
            elif isinstance(out, dict):
                answer = out.get("response", str(out))
                sources = out.get("sources", [])
                generate_quiz = out.get("generate_quiz", False)
                play_quest = out.get("play_quest", False)
            else:
                answer = str(out)
                sources = []
                generate_quiz = False
                play_quest = False

            updated_history = processed_history.copy()
            updated_history.append(ModelRequest(parts=[UserPromptPart(content=user_message)]))
            updated_history.append(ModelResponse(parts=[TextPart(content=answer)]))

            await save_chat_history_to_storage(
                chat_history=updated_history,
                user_id=user_id,
                conversation_id=conversation_id,
                chat_type="tutor",
                background=True,
                tutor_document_id=document_id,
            )

            return {
                "answer": answer,
                "sources": sources,
                "generate_quiz": generate_quiz,
                "play_quest": play_quest,
                "document_id": document_id,
                "enrollment_id": enrollment_id,
                "usage": result.usage().dict()
                if hasattr(result, "usage") and callable(result.usage)
                else {},
            }
        except Exception as e:
            logger.error("Tutor agent error: %s", e)
            return {
                "answer": "I encountered an error while processing your question. Please try again.",
                "sources": [],
                "generate_quiz": False,
                "play_quest": False,
                "document_id": document_id,
                "enrollment_id": enrollment_id,
                "usage": {},
            }


_tutor_agent: Optional[TutorAgent] = None


def get_tutor_agent(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google",
) -> TutorAgent:
    global _tutor_agent
    if _tutor_agent is None:
        _tutor_agent = TutorAgent(model_name, api_key, provider)
    return _tutor_agent


def get_rag_agent(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google",
) -> TutorAgent:
    return get_tutor_agent(model_name, api_key, provider)
