from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.auth import authenticated_user
from app.database import get_db
from app.encar.catalog import CatalogService


router = APIRouter(
    prefix="/api/catalog",
    tags=["Catalog"],
)


catalog_service = CatalogService()


# =========================================================
# MANUFACTURERS
# =========================================================

@router.get("/manufacturers")
def get_manufacturers(
    _user = Depends(authenticated_user),
    db: Session = Depends(get_db),
):
    return catalog_service.get_manufacturers(
        db
    )


# =========================================================
# MODELS
# =========================================================

@router.get("/models")
async def get_models(
    manufacturer: str,
    db: Session = Depends(get_db),
):

    if not manufacturer.strip():
        raise HTTPException(
            status_code=400,
            detail="Не указана марка автомобиля.",
        )


    return await catalog_service.get_models(
        manufacturer=manufacturer,
        db=db,
    )


# =========================================================
# BADGES
# =========================================================

@router.get("/badges")
async def get_badges(
    manufacturer: str,
    model: str,
    db: Session = Depends(get_db),
    _user = Depends(authenticated_user),
):

    if not manufacturer.strip():
        raise HTTPException(
            status_code=400,
            detail="Не указана марка автомобиля.",
        )


    if not model.strip():
        raise HTTPException(
            status_code=400,
            detail="Не указана модель автомобиля.",
        )


    return await catalog_service.get_badges(
        manufacturer=manufacturer,
        model=model,
        db=db,
    )