from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.models.user import User
from app.models.deck import Deck
from app.models.flashcard import Flashcard
from app.models.card_review import CardReview
from app.routers.auth import router as auth_router
from app.routers.decks import router as deck_router
from app.routers.cards import router as card_router
from app.routers.study import router as study_router

app = FastAPI()

# Allow both the local Vite dev server and the deployed production
# frontend to call this API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://flashcard-study-app-r3lr.onrender.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(deck_router)
app.include_router(card_router)
app.include_router(study_router)

Base.metadata.create_all(bind=engine)


# Confirms the server is running
@app.get("/")
def health_check():
    return {"status": "ok"}
