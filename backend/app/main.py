from fastapi import FastAPI
from app.database import Base, engine
from app.models.user import User
from app.models.deck import Deck
from app.models.flashcard import Flashcard
from app.models.card_review import CardReview

app = FastAPI()

Base.metadata.create_all(bind=engine)

# Confirms the server is running
@app.get("/")
def health_check():
    return {"status": "ok"}
