from fastapi import FastAPI

app = FastAPI(title="Test API")

@app.get("/")
def read_root():
    return {"Hello": "World"}
