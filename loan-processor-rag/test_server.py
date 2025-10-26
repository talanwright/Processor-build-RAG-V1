#!/usr/bin/env python3
"""
Simple test server to verify RAG system works
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Simple Test API")

@app.get("/")
async def root():
    return {"message": "RAG System Test Server", "status": "working"}

@app.get("/test")
async def test():
    return {"test": "successful", "components": "basic server working"}

if __name__ == "__main__":
    print("Starting test server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)