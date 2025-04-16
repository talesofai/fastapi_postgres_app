from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ItemBase(BaseModel):
    """项目基础Schema"""
    name: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    """创建项目Schema"""
    pass

class ItemUpdate(BaseModel):
    """更新项目Schema"""
    name: Optional[str] = None
    description: Optional[str] = None

class Item(ItemBase):
    """项目完整Schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 