# backend/app/llm.py
import os
import re
import httpx

# Default qilib "ollama" service nomini ishlatamiz
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
MODEL = os.getenv("LLM_MODEL", "llama3")

async def prompt_to_sql(prompt: str):
    """
    Ollama ga async so'rov yuboradi va (sql, full_text) qaytaradi.
    sql == None bo'lsa SQL topilmagan.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": MODEL,
                "prompt": (
                    "You are an assistant that converts natural language requests into "
                    "valid PostgreSQL SQL queries. The database has these tables:\n"
                    "- clients(id, name, birth_date, region)\n"
                    "- accounts(id, client_id, balance, open_date)\n"
                    "- transactions(id, account_id, amount, date, type)\n\n"
                    "Return only the SQL query when possible. If you cannot produce a SQL, "
                    "explain briefly why. Do NOT add extra commentary when returning SQL.\n\n"
                    f"Request: {prompt}"
                ),
                "stream": False
            }

            resp = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        full_text = f"❌ LLM request error: {e}"
        print(full_text)
        return None, full_text

    # Ollama javobi
    full_text = data.get("response") or data.get("output") or str(data)
    print("LLM full response:\n", full_text)

    sql = extract_sql(full_text)
    if sql:
        print("Extracted SQL:\n", sql)
    else:
        print("No SQL extracted from LLM response.")
    return sql, full_text


def extract_sql(text: str):
    if not text:
        return None

    # ```sql ... ```
    m = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if m:
        return _normalize_sql(m.group(1))

    # "SQL: ..."
    m = re.search(r"SQL[:\s]*([\s\S]*)", text, re.IGNORECASE)
    if m:
        candidate = m.group(1).split("\n\n")[0]
        return _normalize_sql(candidate)

    # SELECT ... ;
    m = re.search(r"(SELECT[\s\S]*?;)", text, re.IGNORECASE)
    if m:
        return _normalize_sql(m.group(1))

    # SELECT ... (without ;)
    m = re.search(r"(SELECT[\s\S]*)", text, re.IGNORECASE)
    if m:
        return _normalize_sql(m.group(1))

    return None


def _normalize_sql(sql: str):
    sql = sql.strip()
    sql = re.sub(r"^```.*", "", sql, flags=re.IGNORECASE)
    sql = sql.strip(" \n;")
    if not sql.endswith(";"):
        sql = sql + ";"
    return sql
