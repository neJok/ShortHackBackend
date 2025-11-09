import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
from applications import router as applications_router
from rooms import router as rooms_router

app = FastAPI(
    title="Univent API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(applications_router, prefix="/applications", tags=["applications"])
app.include_router(rooms_router, prefix="/rooms", tags=["rooms"])

@app.get("/")
async def ping():
    return {"message": "PROOOOOOOOOD!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)