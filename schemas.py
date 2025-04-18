from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Union
from datetime import datetime
import uuid
from uuid import UUID

class ArtifactBase(BaseModel):
    """图片基础Schema"""
    width: int
    height: int
    size: int
    pixels: int
    format: str
    md5: str
    upload_time: int
    update_time: int
    created_time: int
    has_alpha: bool = False
    original_path: str  # 必填字段

class ArtifactCreate(ArtifactBase):
    """创建图片Schema"""
    upload_user: Optional[UUID] = None
    children_id: Optional[List[UUID]] = None
    local_path: Optional[str] = None
    origin_name: Optional[str] = None
    size_2048x_path: Optional[str] = None
    size_1024x_path: Optional[str] = None
    size_256x_path: Optional[str] = None
    
    # 注意：不包含aspect_ratio，因为它是生成列

class ArtifactUpdate(BaseModel):
    """更新图片Schema"""
    upload_time: Optional[int] = None
    update_time: Optional[int] = None
    upload_user: Optional[UUID] = None
    children_id: Optional[List[UUID]] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size: Optional[int] = None
    pixels: Optional[int] = None
    format: Optional[str] = None
    local_path: Optional[str] = None
    origin_name: Optional[str] = None
    original_path: Optional[str] = None  # 更新时可选
    size_2048x_path: Optional[str] = None
    size_1024x_path: Optional[str] = None
    size_256x_path: Optional[str] = None
    is_deleted: Optional[bool] = None
    deleted_time: Optional[str] = None
    
    # 注意：不包含aspect_ratio，因为它是生成列

class Artifact(ArtifactBase):
    """图片完整Schema"""
    id: UUID
    upload_user: Optional[UUID] = None
    children_id: Optional[List[UUID]] = None
    local_path: Optional[str] = None
    origin_name: Optional[str] = None
    aspect_ratio: Optional[float] = None  # 只在响应中包含aspect_ratio
    size_2048x_path: Optional[str] = None
    size_1024x_path: Optional[str] = None
    size_256x_path: Optional[str] = None
    is_deleted: bool
    deleted_time: Optional[str] = None
    
    class Config:
        from_attributes = True

# Collection相关Schema
class CollectionBase(BaseModel):
    """集合基础Schema"""
    name: str
    description: Optional[str] = None
    creator_id: Optional[UUID] = None
    cover_artifact_id: Optional[UUID] = None

class CollectionCreate(CollectionBase):
    """创建集合Schema"""
    pass

class CollectionUpdate(BaseModel):
    """更新集合Schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    creator_id: Optional[UUID] = None
    cover_artifact_id: Optional[UUID] = None
    is_deleted: Optional[bool] = None

class Collection(CollectionBase):
    """集合完整Schema"""
    id: UUID
    create_time: int
    update_time: int
    is_deleted: bool
    deleted_time: Optional[int] = None
    
    class Config:
        from_attributes = True

# ArtifactCollectionMap相关Schema
class ArtifactCollectionMapBase(BaseModel):
    """图片集合映射基础Schema"""
    artifact_id: UUID
    collection_id: UUID
    add_time: int

class ArtifactCollectionMapCreate(BaseModel):
    """创建图片集合映射Schema"""
    artifact_id: UUID
    collection_id: UUID

class ArtifactCollectionMap(ArtifactCollectionMapBase):
    """图片集合映射完整Schema"""
    class Config:
        from_attributes = True

# 嵌套Schema
class CollectionWithArtifacts(Collection):
    """带有图片列表的集合Schema"""
    artifacts: List[Artifact] = []

# 简化后的User相关Schema
class UserLogin(BaseModel):
    """用户登录Schema"""
    username: str
    password: str

class User(BaseModel):
    """用户信息Schema"""
    id: UUID
    username: str
    email: EmailStr
    is_active: bool
    is_superuser: bool
    create_time: datetime
    update_time: datetime
    
    class Config:
        from_attributes = True 