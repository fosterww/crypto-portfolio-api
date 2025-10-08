from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Position, Portfolio, Asset, User
from app.schemas.positions import PositionCreateIn, PositionOut
from app.schemas.common import PaginationParams
from app.core.security import get_current_user

router = APIRouter()

@router.post("", response_model=PositionOut, status_code=status.HTTP_201_CREATED)
def add_position(payload: PositionCreateIn,
                 db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    port = db.get(Portfolio, payload.portfolio_id)
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    asset = db.get(Asset, payload.asset_id)
    if asset is None:
        asset = Asset(id=payload.asset_id, symbol=f"ASSET_{payload.asset_id}", coingecko_id=f"asset_{payload.asset_id}")
        db.add(asset)
        db.flush()
    pos = Position(
        portfolio_id=payload.portfolio_id,
        asset_id=payload.asset_id,
        qty=payload.qty,
        avg_buy_price=payload.avg_buy_price,
    )
    db.add(pos)
    db.commit()
    db.refresh(pos)
    return pos


@router.get("", response_model=list[PositionOut])
def list_positions(portfolio_id: int,
                   p: PaginationParams = Depends(),
                   db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    if not db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.user_id == user.id).first():
        raise HTTPException(status_code=404, detail="Portfolio not found")
    q = (db.query(Position)
           .join(Portfolio, Portfolio.id == Position.portfolio_id)
           .filter(Position.portfolio_id == portfolio_id, Portfolio.user_id == user.id)
           .order_by(Position.id.desc())
           .limit(p.limit).offset(p.offset))
    return q.all()

@router.delete("/{position_id}", status_code=204)
def delete_position(position_id: int,
                    db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    pos = (db.query(Position)
             .join(Portfolio, Portfolio.id == Position.portfolio_id)
             .filter(Position.id == position_id, Portfolio.user_id == user.id)
             .first())
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found")
    db.delete(pos); db.commit()
    return
