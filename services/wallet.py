from uuid import UUID
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from models import Wallet
from schemas import WalletCreate

class WalletService:
    def __init__(self, db: Session):
        self.db = db

    def create_wallet(self, user_id: UUID, wallet_data: WalletCreate) -> Wallet:
        currency_code = wallet_data.currency.upper()

        existing_wallet = self.db.query(Wallet).filter(
            Wallet.user_id == user_id, 
            Wallet.currency == currency_code
        ).first()

        if existing_wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"You already have a {currency_code} wallet."
            )

        new_wallet = Wallet(
            user_id=user_id,
            currency=currency_code,
            balance=0
        )

        try:
            self.db.add(new_wallet)
            self.db.commit()
            self.db.refresh(new_wallet)
            return new_wallet
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Could not create wallet."
            )

    def get_my_wallets(self, user_id: UUID) -> List[Wallet]:
        return self.db.query(Wallet).filter(Wallet.user_id == user_id).all()

    def get_wallet(self, user_id: UUID, currency: str) -> Wallet:
        wallet = self.db.query(Wallet).filter(
            Wallet.user_id == user_id, 
            Wallet.currency == currency.upper()
        ).first()
        
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"No {currency.upper()} wallet found."
            )
        return wallet
