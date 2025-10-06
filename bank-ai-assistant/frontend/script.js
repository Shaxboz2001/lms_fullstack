async function sendQuery() {
  const prompt = document.getElementById("prompt").value;
  const resultDiv = document.getElementById("result");

  resultDiv.innerText = "So‘rov yuborilmoqda...";

  try {
    const response = await fetch("http://localhost:8000/query?prompt=" + encodeURIComponent(prompt), {
      method: "POST"
    });

    if (!response.ok) {
      throw new Error("Server xatosi: " + response.status);
    }

    const data = await response.json();

    if (data.excel_file) {
      resultDiv.innerHTML =
        "✅ SQL: <pre>" + data.sql + "</pre>" +
        "<br>LLM javobi: <pre>" + data.llm_response + "</pre>" +
        `<br><a href="http://localhost:8000/download?file=${encodeURIComponent(data.excel_file)}" download="query_result.xlsx">📥 Excelni yuklab olish</a>`;
    } else {
      resultDiv.innerHTML = "❌ SQL topilmadi.<br><br>LLM javobi:<br><pre>" + data.llm_response + "</pre>";
    }
  } catch (err) {
    resultDiv.innerText = "Xato: " + err.message;
  }
}
