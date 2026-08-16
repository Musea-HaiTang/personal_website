from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.nav import NavCategory, NavLink
from app.schemas.nav import (
    NavCategoryCreate,
    NavCategoryOut,
    NavCategoryUpdate,
    NavLinkCreate,
    NavLinkOut,
    NavLinkUpdate,
)
from app.services import favicon as favicon_service

router = APIRouter(prefix="/api/nav", tags=["nav"])


def _get_category_or_404(db: Session, category_id: int) -> NavCategory:
    category = db.get(NavCategory, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    return category


def _get_link_or_404(db: Session, link_id: int) -> NavLink:
    link = db.get(NavLink, link_id)
    if link is None:
        raise HTTPException(status_code=404, detail="链接不存在")
    return link


@router.get("/categories", response_model=list[NavCategoryOut])
def list_categories(db: Session = Depends(get_db)):
    stmt = (
        select(NavCategory)
        .options(selectinload(NavCategory.links))
        .order_by(NavCategory.sort_order, NavCategory.id)
    )
    return db.scalars(stmt).all()


@router.post("/categories", response_model=NavCategoryOut, status_code=201)
def create_category(payload: NavCategoryCreate, db: Session = Depends(get_db)):
    category = NavCategory(name=payload.name, sort_order=payload.sort_order)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=NavCategoryOut)
def update_category(category_id: int, payload: NavCategoryUpdate, db: Session = Depends(get_db)):
    category = _get_category_or_404(db, category_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = _get_category_or_404(db, category_id)
    db.delete(category)
    db.commit()


@router.get("/links", response_model=list[NavLinkOut])
def list_links(db: Session = Depends(get_db)):
    stmt = select(NavLink).order_by(NavLink.is_pinned.desc(), NavLink.sort_order, NavLink.id)
    return db.scalars(stmt).all()


@router.get("/favicons")
def get_favicon(domain: str):
    """返回本地缓存的网站图标；未缓存或过期时先抓取一次（缓存 7 天）。"""
    clean = favicon_service.sanitize_domain(domain)
    if clean is None:
        raise HTTPException(status_code=400, detail="域名格式不正确")
    path = favicon_service.fetch_and_cache(clean)
    if path is None:
        raise HTTPException(status_code=404, detail="未能获取网站图标")
    return FileResponse(
        path,
        media_type=favicon_service.media_type_for(path),
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.post("/links", response_model=NavLinkOut, status_code=201)
def create_link(payload: NavLinkCreate, db: Session = Depends(get_db)):
    _get_category_or_404(db, payload.category_id)
    link = NavLink(**payload.model_dump())
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.put("/links/{link_id}", response_model=NavLinkOut)
def update_link(link_id: int, payload: NavLinkUpdate, db: Session = Depends(get_db)):
    link = _get_link_or_404(db, link_id)
    data = payload.model_dump(exclude_unset=True)
    if "category_id" in data:
        if data["category_id"] is None:
            raise HTTPException(status_code=400, detail="链接必须属于一个分类")
        _get_category_or_404(db, data["category_id"])
    for key, value in data.items():
        setattr(link, key, value)
    db.commit()
    db.refresh(link)
    return link


@router.delete("/links/{link_id}", status_code=204)
def delete_link(link_id: int, db: Session = Depends(get_db)):
    link = _get_link_or_404(db, link_id)
    db.delete(link)
    db.commit()
