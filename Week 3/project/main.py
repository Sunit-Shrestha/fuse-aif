from fastapi import FastAPI
from pydantic import BaseModel

from sql_generator import run_text_to_sql


app = FastAPI(title="AI Text-to-SQL Agent")


class QueryRequest(BaseModel):
    question: str


@app.post("/agent/sql")
def handle_query(request: QueryRequest):
    return run_text_to_sql(request.question, retry_limit=3)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

