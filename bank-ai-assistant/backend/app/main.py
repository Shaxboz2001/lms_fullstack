# backend/app/main.py
import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from .llm import prompt_to_sql
from .db import run_query
from .excel_export import export_to_excel_sync
from starlette.concurrency import run_in_threadpool
import pprint

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Bank AI Assistant is running"}

@app.post("/query")
async def query(prompt: str = Query(...)):
    try:
        print("📌 Prompt received:", prompt)

        # 1) LLM dan SQL va full_text olish (async)
        sql, full_text = await prompt_to_sql(prompt)
        print("LLM response (preview):", (full_text or "")[:500])
        print("Extracted SQL:", sql)

        if not sql:
            return JSONResponse({"sql": None, "excel_file": None, "llm_response": full_text}, status_code=200)

        # 2) DB queryni bajarish (async)
        rows = await run_query(sql)

        # Agar xatolik bo'lsa
        if isinstance(rows, dict) and "error" in rows:
            return JSONResponse({
                "sql": sql,
                "excel_file": None,
                "llm_response": full_text,
                "error": rows["error"]
            }, status_code=500)

        # 2.1) Natijani console-ga chiqarish
        print("📊 Query result preview (first 5 rows):")
        pprint.pprint(rows[:5] if isinstance(rows, list) else rows)

        # 3) Excelga yozish (blocking)
        filename = f"query_result_{os.urandom(4).hex()}.xlsx"
        file_path = await run_in_threadpool(export_to_excel_sync, rows, filename)

        # 4) Foydalanuvchiga JSON orqali natija va fayl nomini qaytarish
        return {
            "sql": sql,
            "rows_preview": rows[:10] if isinstance(rows, list) else rows,  # 10 ta qator preview
            "excel_file": os.path.basename(file_path),
            "llm_response": full_text
        }

    except Exception as e:
        print("Unexpected error in /query:", e)
        return JSONResponse({
            "sql": None,
            "rows_preview": None,
            "excel_file": None,
            "llm_response": None,
            "error": str(e)
        }, status_code=500)

@app.get("/download")
def download(file: str):
    path = os.path.join("exports", file)
    if os.path.exists(path):
        return FileResponse(
            path,
            filename=file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    return JSONResponse({"error": "File not found"}, status_code=404)
