from sqlalchemy import Column, Integer, String, Text, Boolean, Float, BigInteger, ARRAY, UUID, ForeignKey, DateTime
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

class Collection(Base):
    """集合模型"""
    __tablename__ = "collections"
    __table_args__ = {'extend_existing': True}
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    create_time = Column(BigInteger, nullable=True)
    update_time = Column(BigInteger, nullable=True)
    creator_id = Column(PostgresUUID(as_uuid=True), nullable=True)
    cover_artifact_id = Column(PostgresUUID(as_uuid=True), nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_time = Column(BigInteger, nullable=True)

class ArtifactCollectionMap(Base):
    """图片集合映射模型"""
    __tablename__ = "artifact_collection_map"
    __table_args__ = {'extend_existing': True}
    
    artifact_id = Column(PostgresUUID(as_uuid=True), ForeignKey("artifacts.id", ondelete="CASCADE"), primary_key=True)
    collection_id = Column(PostgresUUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True)
    add_time = Column(BigInteger, nullable=False)

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    create_time = Column(DateTime(timezone=True), nullable=False)
    update_time = Column(DateTime(timezone=True), nullable=False) 