from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.secure import APIKey
from app.models.user import User
from app.core.security import encrypt_value
from app.auth.dependencies import get_current_admin
from pydantic import BaseModel

router = APIRouter(prefix="/api-keys", tags=["Keys"])


class KeyCreate(BaseModel):
    name: str
    value: str


@router.get("/")
async def list_keys(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_admin),
):
    stmt = select(APIKey).where(APIKey.owner_user_id == user.id)
    res = await session.execute(stmt)
    return [
        {"id": k.id, "name": k.name, "masked": "******", "created_at": k.created_at}
        for k in res.scalars().all()
    ]


@router.post("/")
async def create_key(
    data: KeyCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_admin),
):
    ct, nonce, tag = encrypt_value(data.value)
    key = APIKey(
        owner_user_id=user.id, name=data.name, encrypted_key=ct, nonce=nonce, tag=tag
    )
    session.add(key)
    await session.commit()
    return {"status": "ok"}


@router.delete("/{key_id}")
async def delete_key(
    key_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_admin),
):
    key = await session.get(APIKey, key_id)
    if not key or key.owner_user_id != user.id:
        raise HTTPException(status_code=404, detail="Key not found")

    await session.delete(key)
    await session.commit()
    return {"status": "deleted"}
