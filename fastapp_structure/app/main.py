# from fastapi import FastAPI
# from app.api.v1.routes import router


# app = FastAPI()
# app.include_router(router, prefix='/api/v1')

from fastapi import FastAPI
from app.api.v1 import routes
from app.api.v1.auth import router as auth_router


from app.db.database import db  # ✅ import the `db` object, not the module

from app.utils.settings_secheduler import start_scheduler


app = FastAPI(title="Smart Assistant API")

# Route registration
app.include_router(routes.router, prefix="/api/v1", tags=["Chatbot"])



app.include_router(auth_router, prefix="/api/v1")



@app.get("/test-mongo")
def test_mongo():
    try:
        db.command("ping")  # ✅ valid on the actual DB object
        return {"message": "MongoDB connection successful!"}
    except Exception as e:
        return {"error": str(e)}

@app.on_event("startup")
def start_everything():
    start_scheduler()