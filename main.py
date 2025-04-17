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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 