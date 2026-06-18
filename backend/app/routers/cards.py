from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.deck import Deck
from app.models.flashcard import Flashcard
from app.schemas.card import CardCreate, CardUpdate, CardResponse
from app.routers.auth import get_db, get_current_user

router = APIRouter()


@router.get("/decks/{deck_id}/cards", response_model=list[CardResponse])
def get_cards(
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

    return db.query(Flashcard).filter(Flashcard.deck_id == deck_id).all()


@router.get("/decks/{deck_id}/cards/{card_id}", response_model=CardResponse)
def get_card(
    deck_id: int,
    card_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Confirm the deck exists and belongs to the current user
    deck = db.query(Deck).filter(Deck.deck_id == deck_id).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Confirm the card exists in this deck
    card = db.query(Flashcard).filter(
        Flashcard.card_id == card_id,
        Flashcard.deck_id == deck_id
    ).first()
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    return card


@router.post("/decks/{deck_id}/cards", response_model=CardResponse, status_code=201)
def create_card(
    deck_id: int,
    card_data: CardCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Confirm the deck exists and belongs to the current user
    deck = db.query(Deck).filter(Deck.deck_id == deck_id).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Create and persist the new card
    new_card = Flashcard(deck_id=deck_id, question=card_data.question, answer=card_data.answer)
    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    return new_card


@router.patch("/decks/{deck_id}/cards/{card_id}", response_model=CardResponse)
def update_card(
    deck_id: int,
    card_id: int,
    update_data: CardUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Confirm the deck exists and belongs to the current user
    deck = db.query(Deck).filter(Deck.deck_id == deck_id).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Confirm the card exists in this deck
    card = db.query(Flashcard).filter(
        Flashcard.card_id == card_id,
        Flashcard.deck_id == deck_id
    ).first()
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    # Apply only the fields that were provided
    if update_data.question is not None:
        card.question = update_data.question
    if update_data.answer is not None:
        card.answer = update_data.answer

    db.commit()
    db.refresh(card)

    return card


@router.delete("/decks/{deck_id}/cards/{card_id}", status_code=204)
def delete_card(
    deck_id: int,
    card_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Confirm the deck exists and belongs to the current user
    deck = db.query(Deck).filter(Deck.deck_id == deck_id).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Confirm the card exists in this deck
    card = db.query(Flashcard).filter(
        Flashcard.card_id == card_id,
        Flashcard.deck_id == deck_id
    ).first()
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    db.delete(card)
    db.commit()
