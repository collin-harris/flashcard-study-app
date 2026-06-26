from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.deck import Deck
from app.models.flashcard import Flashcard
from app.schemas.deck import DeckCreate, DeckUpdate, DeckResponse, DeckWithCardCount
from app.routers.auth import get_db, get_current_user

router = APIRouter()


@router.get("/decks", response_model=list[DeckWithCardCount])
def get_decks(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Return only the decks owned by the current user, each annotated with its
    # card count via a single outer-joined, grouped query (not one query per deck)
    results = (
        db.query(Deck, func.count(Flashcard.card_id))
        .outerjoin(Flashcard, Flashcard.deck_id == Deck.deck_id)
        .filter(Deck.user_id == current_user.user_id)
        .group_by(Deck.deck_id)
        .order_by(Deck.deck_id)
        .all()
    )

    return [
        DeckWithCardCount(
            deck_id=deck.deck_id,
            user_id=deck.user_id,
            name=deck.name,
            card_count=card_count,
        )
        for deck, card_count in results
    ]


@router.get("/decks/{deck_id}", response_model=DeckResponse)
def get_deck(
    deck_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Confirm the deck exists and belongs to the current user
    deck = db.query(Deck).filter(Deck.deck_id == deck_id).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return deck


@router.post("/decks", response_model=DeckResponse, status_code=201)
def create_deck(
    deck_data: DeckCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Create and persist the new deck
    new_deck = Deck(user_id=current_user.user_id, name=deck_data.name)
    db.add(new_deck)
    db.commit()
    db.refresh(new_deck)

    return new_deck


@router.patch("/decks/{deck_id}", response_model=DeckResponse)
def update_deck(
    deck_id: int,
    update_data: DeckUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Confirm the deck exists and belongs to the current user
    deck = db.query(Deck).filter(Deck.deck_id == deck_id).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Apply only the fields that were provided
    if update_data.name is not None:
        deck.name = update_data.name

    db.commit()
    db.refresh(deck)

    return deck


@router.delete("/decks/{deck_id}", status_code=204)
def delete_deck(
    deck_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Confirm the deck exists and belongs to the current user
    deck = db.query(Deck).filter(Deck.deck_id == deck_id).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(deck)
    db.commit()
