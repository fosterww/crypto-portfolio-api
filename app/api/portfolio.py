from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Portfolio, User
from app.schemas.portfolio import PortfolioCreateIn, PortfolioUpdate, PortfolioOut
from app.schemas.common import PaginationParams
from app.core.security import get_current_user

router = APIRouter()

@router.post("", response_model=PortfolioOut, status_code=201)
def create_portfolio(payload: PortfolioCreateIn,
                     db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    p = Portfolio(user_id=user.id, name=payload.name)
    db.add(p); db.commit(); db.refresh(p)
    return p

@router.patch("/{pid}", response_model=PortfolioOut)
def patch_portfolio(pid: int, payload: PortfolioUpdate,
                    db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    p = db.query(Portfolio).filter(Portfolio.id == pid, Portfolio.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    p.name = payload.name
    db.commit(); db.refresh(p)
    return p

@router.get("", response_model=list[PortfolioOut])
def list_portfolios(p: PaginationParams = Depends(),
                    db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    q = (db.query(Portfolio)
           .filter(Portfolio.user_id == user.id)
           .order_by(Portfolio.id.desc())
           .limit(p.limit).offset(p.offset))
    return q.all()

@router.get("/", response_model=list[PortfolioOut])
def list_portfolios_alias(p: PaginationParams = Depends(),
                          db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)):
    return list_portfolios(p=p, db=db, user=user)

@router.get("/{pid}", response_model=PortfolioOut)
def get_portfolio(pid: int,
                  db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    p = db.query(Portfolio).filter(Portfolio.id == pid, Portfolio.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return p

@router.put("/{pid}", response_model=PortfolioOut)
def update_portfolio(pid: int, payload: PortfolioUpdate,
                     db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    p = db.query(Portfolio).filter(Portfolio.id == pid, Portfolio.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    p.name = payload.name
    db.commit(); db.refresh(p)
    return p

@router.delete("/{pid}", status_code=204)
def delete_portfolio(pid: int,
                     db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    p = db.query(Portfolio).filter(Portfolio.id == pid, Portfolio.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(p); db.commit()
    return
