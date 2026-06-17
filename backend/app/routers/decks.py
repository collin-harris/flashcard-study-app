from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.deck import Deck
from app.schemas.deck import DeckCreate, DeckUpdate, DeckResponse
from app.routers.auth import get_db, get_current_user

router = APIRouter()

@router.get("/decks", response_model=list[DeckResponse])
def get_decks(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(Deck).filter(Deck.user_id == current_user.user_id).all()

@router.get("/decks/{deck_id}", response_model=DeckResponse)
def get_deck(deck_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    deck = db.query(Deck).filter(Deck.deck_id == deck_id).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return deck

@router.post("/decks", response_model=DeckResponse, status_code=201)
def create_deck(deck_data: DeckCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    new_deck = Deck(user_id=current_user.user_id, name=deck_data.name)
    db.add(new_deck)
    db.commit()
    db.refresh(new_deck)
    return new_deck

@router.patch("/decks/{deck_id}", response_model=DeckResponse)
def update_deck(deck_id: int, update_data: DeckUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    deck = db.query(Deck).filter(Deck.deck_id == deck_id).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if update_data.name is not None:
        deck.name = update_data.name
    db.commit()
    db.refresh(deck)
    return deck

@router.delete("/decks/{deck_id}", status_code=204)
def delete_deck(deck_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    deck = db.query(Deck).filter(Deck.deck_id == deck_id).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(deck)
    db.commit()