from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.utils.auth import verify_password, create_access_token, get_current_user

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT id, username, password_hash, role, full_name, is_active FROM users WHERE username = :u"),
        {"u": req.username},
    ).fetchone()

    if not row or not row[5] or not verify_password(req.password, row[2]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": row[1], "role": row[3]})
    return TokenResponse(
        access_token=token,
        role=row[3],
        full_name=row[4],
        username=row[1],
    )


@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT id, username, email, role, full_name, is_active FROM users WHERE id = :id"),
        {"id": current_user["id"]},
    ).fetchone()
    return UserOut(
        id=row[0], username=row[1], email=row[2],
        role=row[3], full_name=row[4], is_active=bool(row[5]),
    )
