from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import text
from uuid import UUID
import uvicorn
import time

from database import engine, get_db, Base
import models
import schemas

# 创建数据库表（已经存在的不会重复创建）
# Base.metadata.create_all(bind=engine)  # 注释掉，因为表已经存在

# 初始化FastAPI应用
app = FastAPI(title="Artifacts API", description="FastAPI与PostgreSQL的图片数据CRUD API")

# 根路由 - 测试连接
@app.get("/")
def read_root():
    return {"status": "success", "message": "API正常运行"}

@app.post("/test-connection/")
def test_connection(db: Session = Depends(get_db)):
    try:
        # 修复：使用SQLAlchemy的text函数来执行原始SQL
        # 尝试执行简单查询
        db.execute(text("SELECT 1"))
        return {"status": "success", "message": "数据库连接成功"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据库连接失败: {str(e)}"
        )

# 创建新图片
@app.post("/artifacts/", response_model=schemas.Artifact, status_code=status.HTTP_201_CREATED)
def create_artifact(artifact: schemas.ArtifactCreate, db: Session = Depends(get_db)):
    # 检查MD5是否已存在
    existing_artifact = db.query(models.Artifact).filter(models.Artifact.md5 == artifact.md5).first()
    if existing_artifact:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"具有相同MD5的图片已存在: {existing_artifact.id}"
        )
    
    # 准备数据
    try:
        # 创建Artifact对象，确保不包含aspect_ratio字段
        artifact_dict = {k: v for k, v in artifact.model_dump().items() if k != 'aspect_ratio'}
        db_artifact = models.Artifact(**artifact_dict)
        
        # 添加到数据库
        db.add(db_artifact)
        db.commit()
        db.refresh(db_artifact)
        
        return db_artifact
    except Exception as e:
        db.rollback()
        print(f"创建图片时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建图片失败: {str(e)}"
        )

# 获取所有图片（支持分页和过滤）
@app.get("/artifacts/", response_model=List[schemas.Artifact])
def read_artifacts(
    skip: int = 0, 
    limit: int = 100, 
    format: Optional[str] = None,
    min_width: Optional[int] = None,
    max_width: Optional[int] = None,
    min_height: Optional[int] = None,
    max_height: Optional[int] = None,
    include_deleted: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(models.Artifact)
    
    # 应用过滤条件
    if not include_deleted:
        query = query.filter(models.Artifact.is_deleted == False)
    if format:
        query = query.filter(models.Artifact.format == format)
    if min_width:
        query = query.filter(models.Artifact.width >= min_width)
    if max_width:
        query = query.filter(models.Artifact.width <= max_width)
    if min_height:
        query = query.filter(models.Artifact.height >= min_height)
    if max_height:
        query = query.filter(models.Artifact.height <= max_height)
    
    # 应用排序和分页
    query = query.order_by(models.Artifact.upload_time.desc())
    artifacts = query.offset(skip).limit(limit).all()
    
    return artifacts

# 获取单个图片
@app.get("/artifacts/{artifact_id}", response_model=schemas.Artifact)
def read_artifact(artifact_id: UUID, db: Session = Depends(get_db)):
    db_artifact = db.query(models.Artifact).filter(models.Artifact.id == artifact_id).first()
    if db_artifact is None:
        raise HTTPException(status_code=404, detail="图片不存在")
    return db_artifact

# 更新图片
@app.put("/artifacts/{artifact_id}", response_model=schemas.Artifact)
def update_artifact(artifact_id: UUID, artifact: schemas.ArtifactUpdate, db: Session = Depends(get_db)):
    db_artifact = db.query(models.Artifact).filter(models.Artifact.id == artifact_id).first()
    if db_artifact is None:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    # 更新时间戳
    update_data = artifact.model_dump(exclude_unset=True)
    
    # 移除aspect_ratio字段（这是数据库生成列）
    if "aspect_ratio" in update_data:
        del update_data["aspect_ratio"]
    
    try:
        # 更新图片属性，确保不更新aspect_ratio
        for key, value in update_data.items():
            if key != "aspect_ratio":  # 额外检查，确保不设置aspect_ratio
                setattr(db_artifact, key, value)
        
        db.commit()
        db.refresh(db_artifact)
        return db_artifact
    except Exception as e:
        db.rollback()
        print(f"更新图片时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新图片失败: {str(e)}"
        )

# 软删除图片
@app.delete("/artifacts/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artifact(artifact_id: UUID, permanent: bool = False, db: Session = Depends(get_db)):
    db_artifact = db.query(models.Artifact).filter(models.Artifact.id == artifact_id).first()
    if db_artifact is None:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    if permanent:
        # 永久删除
        db.delete(db_artifact)
    else:
        # 软删除
        db_artifact.is_deleted = True
        db_artifact.deleted_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    
    db.commit()
    return None

# 根据MD5查找图片
@app.get("/artifacts/md5/{md5}", response_model=schemas.Artifact)
def get_artifact_by_md5(md5: str, db: Session = Depends(get_db)):
    db_artifact = db.query(models.Artifact).filter(models.Artifact.md5 == md5).first()
    if db_artifact is None:
        raise HTTPException(status_code=404, detail="未找到具有此MD5的图片")
    return db_artifact

# ============== 集合相关API ==============

# 创建新集合
@app.post("/collections/", response_model=schemas.Collection, status_code=status.HTTP_201_CREATED)
def create_collection(collection: schemas.CollectionCreate, db: Session = Depends(get_db)):
    try:
        # 添加创建和更新时间戳
        current_time = int(time.time())
        collection_dict = collection.model_dump()
        collection_dict["create_time"] = current_time
        collection_dict["update_time"] = current_time
        
        # 创建集合对象
        db_collection = models.Collection(**collection_dict)
        
        # 添加到数据库
        db.add(db_collection)
        db.commit()
        db.refresh(db_collection)
        
        return db_collection
    except Exception as e:
        db.rollback()
        print(f"创建集合时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建集合失败: {str(e)}"
        )

# 获取所有集合（支持分页和过滤）
@app.get("/collections/", response_model=List[schemas.Collection])
def read_collections(
    skip: int = 0, 
    limit: int = 100,
    include_deleted: bool = False,
    creator_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Collection)
    
    # 应用过滤条件
    if not include_deleted:
        query = query.filter(models.Collection.is_deleted == False)
    if creator_id:
        query = query.filter(models.Collection.creator_id == creator_id)
    
    # 应用排序和分页
    query = query.order_by(models.Collection.create_time.desc())
    collections = query.offset(skip).limit(limit).all()
    
    return collections

# 获取单个集合
@app.get("/collections/{collection_id}", response_model=schemas.Collection)
def read_collection(collection_id: UUID, db: Session = Depends(get_db)):
    db_collection = db.query(models.Collection).filter(models.Collection.id == collection_id).first()
    if db_collection is None:
        raise HTTPException(status_code=404, detail="集合不存在")
    return db_collection

# 获取带有图片的集合详情
@app.get("/collections/{collection_id}/with-artifacts", response_model=schemas.CollectionWithArtifacts)
def read_collection_with_artifacts(
    collection_id: UUID, 
    artifact_limit: int = 100,
    db: Session = Depends(get_db)
):
    # 获取集合信息
    db_collection = db.query(models.Collection).filter(models.Collection.id == collection_id).first()
    if db_collection is None:
        raise HTTPException(status_code=404, detail="集合不存在")
    
    # 获取集合中的图片
    artifacts = db.query(models.Artifact).\
        join(models.ArtifactCollectionMap, models.Artifact.id == models.ArtifactCollectionMap.artifact_id).\
        filter(models.ArtifactCollectionMap.collection_id == collection_id).\
        filter(models.Artifact.is_deleted == False).\
        order_by(models.ArtifactCollectionMap.add_time.desc()).\
        limit(artifact_limit).all()
    
    # 构建响应
    collection_data = schemas.Collection.model_validate(db_collection)
    result = schemas.CollectionWithArtifacts(**collection_data.model_dump())
    result.artifacts = artifacts
    
    return result

# 获取集合中的所有图片
@app.get("/collections/{collection_id}/artifacts", response_model=List[schemas.Artifact])
def read_collection_artifacts(
    collection_id: UUID, 
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # 验证集合存在
    db_collection = db.query(models.Collection).filter(models.Collection.id == collection_id).first()
    if db_collection is None:
        raise HTTPException(status_code=404, detail="集合不存在")
    
    # 获取集合中的图片
    artifacts = db.query(models.Artifact).\
        join(models.ArtifactCollectionMap, models.Artifact.id == models.ArtifactCollectionMap.artifact_id).\
        filter(models.ArtifactCollectionMap.collection_id == collection_id).\
        filter(models.Artifact.is_deleted == False).\
        order_by(models.ArtifactCollectionMap.add_time.desc()).\
        offset(skip).limit(limit).all()
    
    return artifacts

# 更新集合
@app.put("/collections/{collection_id}", response_model=schemas.Collection)
def update_collection(collection_id: UUID, collection: schemas.CollectionUpdate, db: Session = Depends(get_db)):
    db_collection = db.query(models.Collection).filter(models.Collection.id == collection_id).first()
    if db_collection is None:
        raise HTTPException(status_code=404, detail="集合不存在")
    
    # 更新时间戳
    update_data = collection.model_dump(exclude_unset=True)
    update_data["update_time"] = int(time.time())
    
    try:
        # 更新集合属性
        for key, value in update_data.items():
            setattr(db_collection, key, value)
        
        db.commit()
        db.refresh(db_collection)
        return db_collection
    except Exception as e:
        db.rollback()
        print(f"更新集合时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新集合失败: {str(e)}"
        )

# 软删除集合
@app.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(collection_id: UUID, permanent: bool = False, db: Session = Depends(get_db)):
    db_collection = db.query(models.Collection).filter(models.Collection.id == collection_id).first()
    if db_collection is None:
        raise HTTPException(status_code=404, detail="集合不存在")
    
    try:
        if permanent:
            # 永久删除
            db.delete(db_collection)
        else:
            # 软删除
            db_collection.is_deleted = True
            db_collection.deleted_time = int(time.time())
        
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        print(f"删除集合时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除集合失败: {str(e)}"
        )

# ============== 图片集合映射相关API ==============

# 添加图片到集合
@app.post("/collections/{collection_id}/artifacts/{artifact_id}", status_code=status.HTTP_201_CREATED)
def add_artifact_to_collection(collection_id: UUID, artifact_id: UUID, db: Session = Depends(get_db)):
    # 检查集合是否存在
    db_collection = db.query(models.Collection).filter(models.Collection.id == collection_id).first()
    if db_collection is None:
        raise HTTPException(status_code=404, detail="集合不存在")
    
    # 检查图片是否存在
    db_artifact = db.query(models.Artifact).filter(models.Artifact.id == artifact_id).first()
    if db_artifact is None:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    # 检查映射是否已存在
    existing_map = db.query(models.ArtifactCollectionMap).filter(
        models.ArtifactCollectionMap.artifact_id == artifact_id,
        models.ArtifactCollectionMap.collection_id == collection_id
    ).first()
    
    if existing_map:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="图片已经在集合中"
        )
    
    try:
        # 创建新映射
        current_time = int(time.time())
        new_map = models.ArtifactCollectionMap(
            artifact_id=artifact_id,
            collection_id=collection_id,
            add_time=current_time
        )
        
        # 如果集合没有封面，将此图片设为封面
        if not db_collection.cover_artifact_id:
            db_collection.cover_artifact_id = artifact_id
            db_collection.update_time = current_time
        
        db.add(new_map)
        db.commit()
        
        return {"status": "success", "message": "图片已添加到集合"}
    except Exception as e:
        db.rollback()
        print(f"添加图片到集合时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加图片到集合失败: {str(e)}"
        )

# 从集合中移除图片
@app.delete("/collections/{collection_id}/artifacts/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_artifact_from_collection(collection_id: UUID, artifact_id: UUID, db: Session = Depends(get_db)):
    # 查找映射
    map_entry = db.query(models.ArtifactCollectionMap).filter(
        models.ArtifactCollectionMap.artifact_id == artifact_id,
        models.ArtifactCollectionMap.collection_id == collection_id
    ).first()
    
    if map_entry is None:
        raise HTTPException(status_code=404, detail="图片不在集合中")
    
    try:
        # 获取集合
        db_collection = db.query(models.Collection).filter(models.Collection.id == collection_id).first()
        
        # 如果移除的是封面图片，需要更新封面
        if db_collection and db_collection.cover_artifact_id == artifact_id:
            # 尝试找另一张图片作为封面
            another_artifact = db.query(models.ArtifactCollectionMap).\
                filter(models.ArtifactCollectionMap.collection_id == collection_id).\
                filter(models.ArtifactCollectionMap.artifact_id != artifact_id).\
                order_by(models.ArtifactCollectionMap.add_time.desc()).\
                first()
            
            if another_artifact:
                db_collection.cover_artifact_id = another_artifact.artifact_id
            else:
                db_collection.cover_artifact_id = None
            
            db_collection.update_time = int(time.time())
        
        # 移除映射
        db.delete(map_entry)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        print(f"从集合中移除图片时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"从集合中移除图片失败: {str(e)}"
        )

# 获取包含特定图片的所有集合
@app.get("/artifacts/{artifact_id}/collections", response_model=List[schemas.Collection])
def get_collections_for_artifact(
    artifact_id: UUID, 
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # 验证图片存在
    db_artifact = db.query(models.Artifact).filter(models.Artifact.id == artifact_id).first()
    if db_artifact is None:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    # 获取包含此图片的集合
    collections = db.query(models.Collection).\
        join(models.ArtifactCollectionMap, models.Collection.id == models.ArtifactCollectionMap.collection_id).\
        filter(models.ArtifactCollectionMap.artifact_id == artifact_id).\
        filter(models.Collection.is_deleted == False).\
        order_by(models.Collection.name).\
        offset(skip).limit(limit).all()
    
    return collections

# 批量添加图片到集合
@app.post("/collections/{collection_id}/artifacts/batch", status_code=status.HTTP_201_CREATED)
def add_artifacts_to_collection_batch(
    collection_id: UUID,
    artifact_ids: List[UUID],
    db: Session = Depends(get_db)
):
    # 检查集合是否存在
    db_collection = db.query(models.Collection).filter(models.Collection.id == collection_id).first()
    if db_collection is None:
        raise HTTPException(status_code=404, detail="集合不存在")
    
    if not artifact_ids:
        raise HTTPException(status_code=400, detail="图片ID列表不能为空")
    
    try:
        current_time = int(time.time())
        added_count = 0
        already_exists_count = 0
        not_found_count = 0
        
        for artifact_id in artifact_ids:
            # 检查图片是否存在
            db_artifact = db.query(models.Artifact).filter(models.Artifact.id == artifact_id).first()
            if not db_artifact:
                not_found_count += 1
                continue
            
            # 检查映射是否已存在
            existing_map = db.query(models.ArtifactCollectionMap).filter(
                models.ArtifactCollectionMap.artifact_id == artifact_id,
                models.ArtifactCollectionMap.collection_id == collection_id
            ).first()
            
            if existing_map:
                already_exists_count += 1
                continue
            
            # 添加新映射
            new_map = models.ArtifactCollectionMap(
                artifact_id=artifact_id,
                collection_id=collection_id,
                add_time=current_time
            )
            db.add(new_map)
            added_count += 1
            
            # 如果集合没有封面，将第一张有效图片设为封面
            if not db_collection.cover_artifact_id and added_count == 1:
                db_collection.cover_artifact_id = artifact_id
                db_collection.update_time = current_time
        
        db.commit()
        
        return {
            "status": "success", 
            "message": f"已添加{added_count}张图片到集合，{already_exists_count}张已存在，{not_found_count}张未找到"
        }
    except Exception as e:
        db.rollback()
        print(f"批量添加图片到集合时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量添加图片到集合失败: {str(e)}"
        )

# ============== 用户相关API ==============

# 根据ID获取用户信息
@app.get("/users/{user_id}", response_model=schemas.User)
def get_user_by_id(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user

# 根据用户名获取用户信息
@app.get("/users/username/{username}", response_model=schemas.User)
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user

# 根据邮箱获取用户信息
@app.get("/users/email/{email}", response_model=schemas.User)
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user

# 获取所有用户（分页）
@app.get("/users/", response_model=List[schemas.User])
def get_users(
    skip: int = 0, 
    limit: int = 100,
    is_active: Optional[bool] = None,
    is_superuser: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.User)
    
    # 应用过滤条件
    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)
    if is_superuser is not None:
        query = query.filter(models.User.is_superuser == is_superuser)
    
    # 应用排序和分页
    users = query.order_by(models.User.username).offset(skip).limit(limit).all()
    return users

# 验证用户凭据（用于登录）
@app.post("/users/login/", response_model=schemas.User)
def login_user(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    用户登录API
    接收用户名和密码，返回用户信息
    """
    # 在实际应用中，密码应该是哈希的，这里假设password字段包含哈希密码
    # 应该使用像passlib这样的库进行密码验证
    user = db.query(models.User).filter(
        models.User.username == user_credentials.username
    ).first()
    
    if not user or user.hashed_password != user_credentials.password:  # 不安全！仅用于演示
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户未激活"
        )
    
    return user

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 