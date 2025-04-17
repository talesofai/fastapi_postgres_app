from sqlalchemy import Column, Integer, String, Text, Boolean, Float, BigInteger, ARRAY, UUID
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
import uuid
from database import Base

class Artifact(Base):
    """图片数据模型"""
    __tablename__ = "artifacts"
    __table_args__ = {'extend_existing': True}
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_time = Column(BigInteger, nullable=False)
    update_time = Column(BigInteger, nullable=False)
    upload_user = Column(PostgresUUID(as_uuid=True), nullable=True)
    children_id = Column(ARRAY(PostgresUUID(as_uuid=True)), nullable=True)
    
    # 元数据字段
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    size = Column(BigInteger, nullable=False)
    pixels = Column(BigInteger, nullable=False)
    format = Column(String(10), nullable=False)
    md5 = Column(String(32), nullable=False, unique=True)
    local_path = Column(String(255), nullable=True)
    origin_name = Column(String(255), nullable=True)
    created_time = Column(BigInteger, nullable=False)
    has_alpha = Column(Boolean, nullable=False, default=False)
    
    # 文件路径
    original_path = Column(Text, nullable=False)
    size_2048x_path = Column(Text, nullable=True)
    size_1024x_path = Column(Text, nullable=True)
    size_256x_path = Column(Text, nullable=True)
    
    # 软删除
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_time = Column(Text, nullable=True)  # 使用Text代替TIMESTAMP WITH TIME ZONE 