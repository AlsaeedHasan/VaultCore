from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import oauth2
import schemas
from database import get_db
from services import TransactionService

router = APIRouter(prefix="/api/v1/transaction", tags=["Transactions"])


@router.post(
    "/deposit",
    response_model=schemas.TransactionResponse,
    status_code=status.HTTP_200_OK,
)
def deposit(
    deposit_request: schemas.DepositRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
):
    transaction_service = TransactionService(db)

    return transaction_service.deposit(
        user_id=current_user.id,
        amount=deposit_request.amount,
        currency=deposit_request.currency,
        description=deposit_request.description or "Deposit",
    )


@router.post(
    "/transfer",
    response_model=schemas.TransactionResponse,
    status_code=status.HTTP_200_OK,
)
def transfer(
    transfer_request: schemas.TransferRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
):
    transaction_service = TransactionService(db)

    return transaction_service.transfer(
        sender_id=current_user.id,
        receiver_email=transfer_request.receiver_email,
        amount=transfer_request.amount,
        currency=transfer_request.currency,
    )


@router.post(
    "/withdraw",
    response_model=schemas.TransactionResponse,
    status_code=status.HTTP_200_OK,
)
def withdraw(
    withdraw_request: schemas.WithdrawRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(oauth2.get_current_active_user),
):
    transaction_service = TransactionService(db)

    return transaction_service.withdraw(
        user_id=current_user.id,
        amount=withdraw_request.amount,
        currency=withdraw_request.currency,
        description=withdraw_request.description or "Withdrawal",
    )
