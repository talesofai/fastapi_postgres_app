from pydantic import BaseModel, Field
from typing import Optional, List, Union, Dict, Any
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

# Caption Preset Schemas
class CaptionPresetBase(BaseModel):
    """预设基础Schema"""
    config: Dict[str, Any]  # 存储模型、提示词等配置信息
    description: Optional[str] = None
    create_time: int

class CaptionPresetCreate(CaptionPresetBase):
    """创建预设Schema"""
    preset_key: str
    creator_id: Optional[UUID] = None

class CaptionPresetUpdate(BaseModel):
    """更新预设Schema"""
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_deleted: Optional[bool] = None
    deleted_time: Optional[int] = None

class CaptionPreset(CaptionPresetBase):
    """预设完整Schema"""
    preset_key: str
    creator_id: Optional[UUID] = None
    is_deleted: bool
    deleted_time: Optional[int] = None

    class Config:
        from_attributes = True

# Caption Schemas
class CaptionBase(BaseModel):
    """描述基础Schema"""
    type: Optional[str] = None
    preset_key: Optional[str] = None
    upload_time: int
    text: Optional[str] = None

class CaptionCreate(CaptionBase):
    """创建描述Schema"""
    extra_data: Optional[Dict[str, Any]] = None

class CaptionUpdate(BaseModel):
    """更新描述Schema"""
    type: Optional[str] = None
    preset_key: Optional[str] = None
    upload_time: Optional[int] = None
    text: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    is_deleted: Optional[bool] = None
    deleted_time: Optional[int] = None

class Caption(CaptionBase):
    """描述完整Schema"""
    id: UUID
    extra_data: Optional[Dict[str, Any]] = None
    is_deleted: bool
    deleted_time: Optional[int] = None

    class Config:
        from_attributes = True

# ArtifactCaptionMap Schemas
class ArtifactCaptionMapBase(BaseModel):
    """映射基础Schema"""
    artifact_id: UUID
    caption_id: UUID
    add_time: int

class ArtifactCaptionMapCreate(ArtifactCaptionMapBase):
    """创建映射Schema"""
    pass

class ArtifactCaptionMap(ArtifactCaptionMapBase):
    """映射完整Schema"""
    class Config:
        from_attributes = True