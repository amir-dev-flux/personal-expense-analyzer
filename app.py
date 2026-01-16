from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import shutil
import os
from fastapi.responses import FileResponse
from urllib3 import request
from src.analyzer import analyze_expenses, generate_pdf_report
from fastapi import UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


from src.analyzer import analyze_expenses

app = FastAPI()

templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(None)):

    # 1. No file selected
        if not file or not file.filename:
            return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Please select a file before clicking Analyze."
        })
    # 2. Invalid file type
        if not (file.filename.endswith(".csv") or file.filename.endswith(".pdf")):
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": "Please upload a valid CSV or HDFC PDF statement."
            })
    # 3. Save file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

    # 4. Run analysis safely
        try:
            results = analyze_expenses(file_path)
        except ValueError as e:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "error": str(e)
            })
        
    # 5. Generate PDF report (THIS WAS MISSING)
        os.makedirs("reports", exist_ok=True)

        report_path = os.path.join("reports", "latest_report.pdf")

        generate_pdf_report(
            results=results,
            output_path=report_path,
            filename=file.filename,
            generated_at=results["generated"]
        )
    # 5. Render success
        return templates.TemplateResponse("index.html", {
            "request": request,
            "results": results,
            "filename": file.filename
        })

@app.get("/download-report")
def download_report():
    pdf_path = "reports/latest_report.pdf"

    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, filename="expense_report.pdf")
    else:
        return {"error": "No report available"}

