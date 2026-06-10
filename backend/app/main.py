from fastapi import FastAPI

app = FastAPI()

# Confirms the server is running
@app.get("/")
def health_check():
    return {"status": "ok"}
