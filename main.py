from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from transformers import pipeline
from fastapi.middleware.cors import CORSMiddleware
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize the summarization pipeline
try:
    summarizer = pipeline("summarization")
    logger.info("Summarization pipeline initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize summarization pipeline: {e}")
    raise e

def summarize_document(content: bytes) -> str:
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error: {e}")
        raise HTTPException(status_code=400, detail="Unsupported file encoding.")

    try:
        summary = summarizer(text, max_length=130, min_length=30, do_sample=False)
    except Exception as e:
        logger.error(f"Unexpected error during summarization: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    return summary[0]['summary_text']

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type != 'text/plain':
        raise HTTPException(status_code=400, detail="Only text files are accepted.")
    
    try:
        content = await file.read()
        logger.info(f"File received: {file.filename}")
        summary = summarize_document(content)
        return JSONResponse(content={"summary": summary})
    except HTTPException as e:
        logger.error(f"HTTP error: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
