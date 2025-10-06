# backend/app/excel_export.py
import os
import pandas as pd
import uuid
from typing import List, Dict

EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

def export_to_excel_sync(rows: List[Dict], filename: str = None) -> str:
    """
    Blocking function — pandas/ExcelWriter ishlatadi.
    Returns full path.
    """
    if filename is None:
        filename = f"query_result_{uuid.uuid4().hex[:8]}.xlsx"
    path = os.path.join(EXPORT_DIR, filename)

    if not rows:
        # bo'sh DataFrame yozamiz (header bo'lmaydi)
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(rows)

    # yozish va oddiy chart qo'shish (agar mos bo'lsa)
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Results", index=False)
        workbook = writer.book
        worksheet = writer.sheets["Results"]

        # agar DataFrame kamida 2 ustun bo'lsa va 1-ustun kategoriyalar bo'lsa
        if not df.empty and df.shape[1] >= 2:
            # chart uchun 1-ustun kategoriyalar, 2-ustun qiymatlar
            try:
                chart = workbook.add_chart({"type": "column"})
                cols = df.columns.tolist()
                # first data column index = 1
                chart.add_series({
                    "name": cols[1],
                    "categories": ['Results', 1, 0, len(df), 0],
                    "values":     ['Results', 1, 1, len(df), 1],
                })
                chart.set_title({"name": "Results Chart"})
                worksheet.insert_chart("H2", chart)
            except Exception as e:
                print("Chart creation skipped:", e)

    return path
