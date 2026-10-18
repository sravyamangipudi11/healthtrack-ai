"""Business logic: cache -> LLM -> validate -> safety rules -> log. No HTTP concerns here."""
import json, time, uuid
from pydantic import ValidationError
from .cache import TTLCache
from .llm import LLMError
from .safety import detect_red_flags, escalate
from .schemas import Insight, InsightResponse, SymptomRequest


def build_prompt(req: SymptomRequest) -> str:
    # user text is JSON-encoded so it is clearly data, not instructions
    return "Patient data (JSON): " + json.dumps(req.model_dump(mode="json", exclude_none=True))


class InsightService:
    def __init__(self, provider, cache: TTLCache, logger):
        self.provider, self.cache, self.logger = provider, cache, logger

    def _call_llm(self, prompt: str) -> Insight:
        last = None
        for _ in range(2):  # one retry on malformed output
            raw = self.provider.generate(prompt)
            try:
                return Insight.model_validate_json(raw)
            except ValidationError as e:
                last = e
        raise LLMError(f"LLM returned invalid output: {last.error_count()} schema errors")

    def analyze(self, req: SymptomRequest, role: str) -> InsightResponse:
        rid, t0 = uuid.uuid4().hex[:12], time.time()
        key = TTLCache.make_key(
            req.symptoms, req.age, req.sex.value, req.duration_days,
            req.temperature, req.temperature_unit
        )
        use_cache = req.notes is None  # notes make a case unique -> bypass cache
        insight = self.cache.get(key) if use_cache else None
        cached = insight is not None
        if insight is None:
            try:
                insight = self._call_llm(build_prompt(req))
            except LLMError as e:
                self.logger.record(
                    request_id=rid,
                    role=role,
                    cached=False,
                    latency_ms=int((time.time() - t0) * 1000),
                    error=str(e),
                )
                raise
            if use_cache:
                self.cache.set(key, insight)
        flags = detect_red_flags(req.symptoms)
        data = insight.model_copy(update={
            "urgency": escalate(insight.urgency, flags),
            "red_flags": list(dict.fromkeys(insight.red_flags + flags)),
        })
        resp = InsightResponse(**data.model_dump(), request_id=rid, cached=cached)
        self.logger.record(request_id=rid, role=role, cached=cached, latency_ms=int((time.time() - t0) * 1000),
                           request={**req.model_dump(mode="json", exclude={"notes"}), "has_notes": req.notes is not None},
                           response=data.model_dump())
        return resp
