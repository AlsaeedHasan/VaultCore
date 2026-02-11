from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

import schemas
import oauth2
from database import get_db
from services import WalletService

router = APIRouter(prefix="/api/v1/wallets", tags=["Wallets"])


@router.post(
    "/",
    response_model=schemas.WalletResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_wallet(
    wallet_data: schemas.WalletCreate,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
):
    wallet_service = WalletService(db)
    return wallet_service.create_wallet(
        user_id=current_user.id, wallet_data=wallet_data
    )


@router.get(
    "/",
    response_model=List[schemas.WalletResponse],
    status_code=status.HTTP_200_OK,
)
def get_my_wallets(
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
):
    wallet_service = WalletService(db)
    return wallet_service.get_my_wallets(user_id=current_user.id)


@router.get(
    "/{currency}",
    response_model=schemas.WalletResponse,
    status_code=status.HTTP_200_OK,
)
def get_wallet(
    currency: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
):
    wallet_service = WalletService(db)
    return wallet_service.get_wallet(user_id=current_user.id, currency=currency)
