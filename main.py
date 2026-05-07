from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import engine, Base
from routers import auth, persons, payments, reports, settings




Base.metadata.create_all(bind=engine)
print("[OK] Database tables initialised.")


app = FastAPI(
title="FinSmart API",
    description="backend API for FinSmart Finance Management.",)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,     prefix="/auth")
app.include_router(persons.router,  prefix="/persons")
app.include_router(payments.router, prefix="/payments")
app.include_router(reports.router,  prefix="/reports")
app.include_router(settings.router, prefix="/settings")



@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the FinSmart API 🚀"}
