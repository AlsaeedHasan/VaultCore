from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from models import Transaction, User, Wallet
from services import WalletService
from utils import TransactionStatus, TransactionType


class TransactionService:
    def __init__(self, db: Session):
        self.db = db

    def deposit(
        self,
        user_id: UUID,
        amount: Decimal,
        currency: str,
        description: str = "Deposit",
    ) -> Transaction:
        wallet = (
            self.db.query(Wallet)
            .filter(Wallet.user_id == user_id, Wallet.currency == currency)
            .with_for_update()
            .first()
        )

        if not wallet:
            raise HTTPException(
                status_code=404, detail=f"No {currency} wallet found for this user"
            )

        wallet.balance += amount

        transaction = Transaction(
            wallet_id=wallet.id,
            amount=amount,
            balance_after=wallet.balance,
            type=TransactionType.DEPOSIT.value,
            status=TransactionStatus.COMPLETED.value,
            description=description,
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def withdraw(
        self,
        user_id: UUID,
        amount: Decimal,
        currency: str,
        description: str = "Withdrawal",
    ) -> Transaction:
        wallet = (
            self.db.query(Wallet)
            .filter(Wallet.user_id == user_id, Wallet.currency == currency)
            .with_for_update()
            .first()
        )

        if not wallet:
            raise HTTPException(
                status_code=404, detail=f"No {currency} wallet found for this user"
            )

        if wallet.balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        wallet.balance -= amount

        transaction = Transaction(
            wallet_id=wallet.id,
            amount=-amount,
            balance_after=wallet.balance,
            type=TransactionType.WITHDRAWAL.value,
            status=TransactionStatus.COMPLETED.value,
            description=description,
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def transfer(
        self, sender_id: UUID, receiver_email: str, amount: Decimal, currency: str
    ) -> Transaction:
        receiver = self.db.query(User).filter(User.email == receiver_email).first()
        if not receiver:
            raise HTTPException(status_code=404, detail="Receiver not found")

        if sender_id == receiver.id:
            raise HTTPException(
                status_code=400, detail="Cannot transfer money to yourself"
            )

        sender_wallet_id_query = (
            self.db.query(Wallet.id)
            .filter(Wallet.user_id == sender_id, Wallet.currency == currency)
            .scalar()
        )
        receiver_wallet_id_query = (
            self.db.query(Wallet.id)
            .filter(Wallet.user_id == receiver.id, Wallet.currency == currency)
            .scalar()
        )

        if not sender_wallet_id_query:
            raise HTTPException(
                status_code=404, detail="You don't have a wallet for this currency"
            )

        if not receiver_wallet_id_query:
            raise HTTPException(
                status_code=404,
                detail="Receiver doesn't have a wallet for this currency",
            )

        first_lock_id, second_lock_id = sorted(
            [sender_wallet_id_query, receiver_wallet_id_query]
        )

        try:
            wallet_1 = (
                self.db.query(Wallet)
                .filter(Wallet.id == first_lock_id)
                .with_for_update()
                .first()
            )
            wallet_2 = (
                self.db.query(Wallet)
                .filter(Wallet.id == second_lock_id)
                .with_for_update()
                .first()
            )

            sender_wallet = (
                wallet_1 if wallet_1.id == sender_wallet_id_query else wallet_2
            )
            receiver_wallet = (
                wallet_2 if wallet_2.id == receiver_wallet_id_query else wallet_1
            )

            if sender_wallet.balance < amount:
                raise HTTPException(status_code=400, detail="Insufficient funds")

            sender_wallet.balance -= amount
            receiver_wallet.balance += amount

            outgoing_tx = Transaction(
                wallet_id=sender_wallet.id,
                amount=-amount,
                balance_after=sender_wallet.balance,
                type=TransactionType.TRANSFER.value,
                status=TransactionStatus.COMPLETED.value,
                description=f"Transfer to {receiver.email}",
            )

            incoming_tx = Transaction(
                wallet_id=receiver_wallet.id,
                amount=amount,
                balance_after=receiver_wallet.balance,
                type=TransactionType.TRANSFER.value,
                status=TransactionStatus.COMPLETED.value,
                description=f"Received from {sender_wallet.user.email}",
            )

            self.db.add(outgoing_tx)
            self.db.add(incoming_tx)

            self.db.flush()

            outgoing_tx.related_transaction_id = incoming_tx.id
            incoming_tx.related_transaction_id = outgoing_tx.id

            self.db.commit()
            self.db.refresh(outgoing_tx)

            return outgoing_tx

        except Exception as e:
            self.db.rollback()
            if isinstance(e, HTTPException):
                raise e

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
