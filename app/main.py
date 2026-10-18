"""HTTP layer: routes, wiring, error mapping."""
from pathlib import Path
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from .auth import make_auth
from .cache import TTLCache
from .config import Settings
from .llm import LLMError, build_provider
from .logging_utils import InteractionLogger
from .schemas import InsightResponse, SymptomRequest
from .service import InsightService
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

INDEX = (Path(__file__).parent / "templates" / "index.html").read_text()


def create_app(settings: Optional[Settings] = None, provider=None) -> FastAPI:
    s = settings or Settings()
    service = InsightService(provider or build_provider(s), TTLCache(s.cache_ttl), InteractionLogger(s.log_path))
    require = make_auth(s)
    app = FastAPI(title="HealthTrack AI")

    @app.get("/", response_class=HTMLResponse)
    def index():
        return INDEX

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/analyze", response_model=InsightResponse)
    def analyze(req: SymptomRequest, role: str = Depends(require("clinician", "admin"))):
        try:
            return service.analyze(req, role)
        except LLMError:
            raise HTTPException(502, "AI service unavailable or returned invalid output; try again")

    @app.get("/api/logs")
    def logs(n: int = 50, role: str = Depends(require("admin"))):
        return service.logger.tail(min(n, 200))


    @app.exception_handler(RequestValidationError)
    async def on_validation_error(request: Request, exc: RequestValidationError):
        service.logger.record(
            event="validation_rejected",
            errors=[
                {"loc": list(e["loc"]), "msg": e["msg"]}
                for e in exc.errors()
            ],
        )
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    return app


app = create_app()
