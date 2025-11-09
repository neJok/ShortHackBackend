import uvicorn
from fastapi import FastAPI
from auth import router as auth_router

app = FastAPI(
    title="Univent API",
    version="0.1.0",
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.get("/")
async def ping():
    return {"message": "PROOOOOOOOOD!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)