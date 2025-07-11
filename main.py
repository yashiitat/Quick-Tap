from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import models
import schemas
import database
import auth

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = auth.hash_password(user.password)
    new_user = models.User(email=user.email, password_hash=hashed_pw)
    db.add(new_user)
    db.commit()
    return {"message": "Signup successful"}

@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not auth.verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"user_id": str(db_user.id)}

@app.post("/score")
def submit_score(score_data: schemas.ScoreSubmit, user_id: str, db: Session = Depends(get_db)):
    score = models.Score(user_id=user_id, score=score_data.score)
    db.add(score)
    db.commit()
    return {"message": "Score submitted!"}

@app.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    scores = (
        db.query(models.Score)
        .order_by(models.Score.score.desc())
        .limit(10)
        .all()
    )
    return [{"score": s.score, "timestamp": s.created_at} for s in scores] 

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
