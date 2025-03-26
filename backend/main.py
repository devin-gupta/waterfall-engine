from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:80", "http://localhost:3000"],  # Updated ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")  # Updated path to match healthcheck
async def health_check():
    return {"status": "healthy"}

@app.get("/")  # Add root endpoint
async def read_root():
    return {"message": "API is running"}

@app.get("/api/hello")
async def hello_world():
    return {"message": "Hello from FastAPI!"}
