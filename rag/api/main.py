from fastapi import FastAPI
from pydantic import BaseModel
from core.generator import generate_migration_bundle

app = FastAPI()


class GenerateInput(BaseModel):
    request_text: str
    project_root: str = "."


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate-migration")
def generate_migration(data: GenerateInput):
    return generate_migration_bundle(data.request_text, data.project_root)