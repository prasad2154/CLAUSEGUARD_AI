import os
import sys
import traceback

out_file = "d:/AI COURSE/G_38/CLAUSEGUARD_AI/test_extract_out.txt"

with open(out_file, "w", encoding="utf-8") as f:
    try:
        sys.path.insert(0, os.path.abspath("backend"))
        f.write("Importing pdf_processor and pipeline...\n")
        from app.ingestion.pdf_processor import extract_pdf
        from app.ingestion.pipeline import run_ingestion_pipeline

        file_path = "sample_master_services_agreement.pdf"
        f.write(f"Checking {file_path}, exists: {os.path.exists(file_path)}\n")
        if os.path.exists(file_path):
            res = extract_pdf(file_path)
            f.write(f"Total pages: {res.total_pages}\n")
            f.write(f"Total chars: {res.total_chars}\n")
            f.write(f"Needs OCR: {res.needs_ocr}\n")
            f.write(f"Error: {res.error}\n")
            f.write(f"Sample text: {res.full_text[:300]}\n")

            pipeline_res = run_ingestion_pipeline(file_path, "sample_master_services_agreement.pdf", os.path.getsize(file_path))
            f.write(f"Pipeline success: {pipeline_res.success}\n")
            f.write(f"Pipeline clauses count: {pipeline_res.clause_count}\n")
            f.write(f"Pipeline error: {pipeline_res.error}\n")
            f.write(f"Pipeline contract_type: {pipeline_res.contract_type}\n")
            for idx, cl in enumerate(pipeline_res.clauses[:3]):
                f.write(f"Clause {idx}: {cl.clause_id} - {cl.clause_title}\n")
    except Exception as e:
        f.write(f"EXCEPTION: {e}\n")
        f.write(traceback.format_exc())
