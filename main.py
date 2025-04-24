from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
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

# Caption Preset API
@app.post("/presets/", response_model=schemas.CaptionPreset, status_code=status.HTTP_201_CREATED)
def create_preset(preset: schemas.CaptionPresetCreate, db: Session = Depends(get_db)):
    # 检查预设是否已存在
    existing_preset = db.query(models.CaptionPreset).filter(models.CaptionPreset.preset_key == preset.preset_key).first()
    if existing_preset and not existing_preset.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"具有相同键的预设已存在: {preset.preset_key}"
        )

    # 如果存在但已删除，则恢复并更新
    if existing_preset and existing_preset.is_deleted:
        for key, value in preset.model_dump().items():
            setattr(existing_preset, key, value)
        existing_preset.is_deleted = False
        existing_preset.deleted_time = None
        db.commit()
        db.refresh(existing_preset)
        return existing_preset

    # 创建新预设
    try:
        db_preset = models.CaptionPreset(**preset.model_dump())
        db.add(db_preset)
        db.commit()
        db.refresh(db_preset)
        return db_preset
    except Exception as e:
        db.rollback()
        print(f"创建预设时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建预设失败: {str(e)}"
        )

@app.get("/presets/", response_model=List[schemas.CaptionPreset])
def read_presets(skip: int = 0, limit: int = 100, include_deleted: bool = False, db: Session = Depends(get_db)):
    query = db.query(models.CaptionPreset)

    # 应用过滤条件
    if not include_deleted:
        query = query.filter(models.CaptionPreset.is_deleted == False)

    # 应用排序和分页
    query = query.order_by(models.CaptionPreset.create_time.desc())
    presets = query.offset(skip).limit(limit).all()

    return presets

@app.get("/presets/{preset_key}", response_model=schemas.CaptionPreset)
def read_preset(preset_key: str, db: Session = Depends(get_db)):
    db_preset = db.query(models.CaptionPreset).filter(
        models.CaptionPreset.preset_key == preset_key,
        models.CaptionPreset.is_deleted == False
    ).first()

    if db_preset is None:
        raise HTTPException(status_code=404, detail="预设不存在")

    return db_preset

@app.put("/presets/{preset_key}", response_model=schemas.CaptionPreset)
def update_preset(preset_key: str, preset: schemas.CaptionPresetUpdate, db: Session = Depends(get_db)):
    db_preset = db.query(models.CaptionPreset).filter(models.CaptionPreset.preset_key == preset_key).first()
    if db_preset is None:
        raise HTTPException(status_code=404, detail="预设不存在")

    try:
        # 更新预设属性
        update_data = preset.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_preset, key, value)

        db.commit()
        db.refresh(db_preset)
        return db_preset
    except Exception as e:
        db.rollback()
        print(f"更新预设时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新预设失败: {str(e)}"
        )

@app.delete("/presets/{preset_key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preset(preset_key: str, permanent: bool = False, db: Session = Depends(get_db)):
    db_preset = db.query(models.CaptionPreset).filter(models.CaptionPreset.preset_key == preset_key).first()
    if db_preset is None:
        raise HTTPException(status_code=404, detail="预设不存在")

    try:
        if permanent:
            # 永久删除
            db.delete(db_preset)
        else:
            # 软删除
            db_preset.is_deleted = True
            db_preset.deleted_time = int(time.time() * 1000)  # 使用毫秒时间戳

        db.commit()
        return None
    except Exception as e:
        db.rollback()
        print(f"删除预设时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除预设失败: {str(e)}"
        )

# Caption API
@app.post("/captions/", response_model=schemas.Caption, status_code=status.HTTP_201_CREATED)
def create_caption(caption: schemas.CaptionCreate, db: Session = Depends(get_db)):

    # 如果指定了preset_key，检查预设是否存在
    if caption.preset_key:
        db_preset = db.query(models.CaptionPreset).filter(
            models.CaptionPreset.preset_key == caption.preset_key,
            models.CaptionPreset.is_deleted == False
        ).first()
        if db_preset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"预设不存在: {caption.preset_key}"
            )

    # 检查是否已存在相同预设的描述
    if caption.preset_key:
        existing_caption = db.query(models.Caption).filter(
            models.Caption.preset_key == caption.preset_key,
            models.Caption.is_deleted == False
        ).first()

        # 如果存在，则更新
        if existing_caption:
            update_data = caption.model_dump(exclude={"id"} if hasattr(caption, "id") else set())
            for key, value in update_data.items():
                setattr(existing_caption, key, value)

            db.commit()
            db.refresh(existing_caption)
            return existing_caption

    # 创建新描述
    try:
        caption_dict = caption.model_dump()
        db_caption = models.Caption(**caption_dict)
        db.add(db_caption)
        db.commit()
        db.refresh(db_caption)
        return db_caption
    except Exception as e:
        db.rollback()
        print(f"创建描述时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建描述失败: {str(e)}"
        )

@app.get("/captions/", response_model=List[schemas.Caption])
def read_captions(skip: int = 0, limit: int = 100, include_deleted: bool = False, db: Session = Depends(get_db)):
    query = db.query(models.Caption)

    # 应用过滤条件
    if not include_deleted:
        query = query.filter(models.Caption.is_deleted == False)

    # 应用排序和分页
    query = query.order_by(models.Caption.upload_time.desc())
    captions = query.offset(skip).limit(limit).all()

    return captions

@app.get("/captions/{caption_id}", response_model=schemas.Caption)
def read_caption(caption_id: UUID, db: Session = Depends(get_db)):
    db_caption = db.query(models.Caption).filter(
        models.Caption.id == caption_id,
        models.Caption.is_deleted == False
    ).first()

    if db_caption is None:
        raise HTTPException(status_code=404, detail="描述不存在")

    return db_caption

@app.get("/captions/preset/{preset_key}", response_model=schemas.Caption)
def read_caption_by_preset(preset_key: str, db: Session = Depends(get_db)):
    db_caption = db.query(models.Caption).filter(
        models.Caption.preset_key == preset_key,
        models.Caption.is_deleted == False
    ).first()

    if db_caption is None:
        raise HTTPException(status_code=404, detail="描述不存在")

    return db_caption

@app.put("/captions/{caption_id}", response_model=schemas.Caption)
def update_caption(caption_id: UUID, caption: schemas.CaptionUpdate, db: Session = Depends(get_db)):
    db_caption = db.query(models.Caption).filter(models.Caption.id == caption_id).first()
    if db_caption is None:
        raise HTTPException(status_code=404, detail="描述不存在")

    try:
        # 更新描述属性
        update_data = caption.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_caption, key, value)

        db.commit()
        db.refresh(db_caption)
        return db_caption
    except Exception as e:
        db.rollback()
        print(f"更新描述时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新描述失败: {str(e)}"
        )

@app.delete("/captions/{caption_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_caption(caption_id: UUID, permanent: bool = False, db: Session = Depends(get_db)):
    db_caption = db.query(models.Caption).filter(models.Caption.id == caption_id).first()
    if db_caption is None:
        raise HTTPException(status_code=404, detail="描述不存在")

    try:
        if permanent:
            # 永久删除
            db.delete(db_caption)
        else:
            # 软删除
            db_caption.is_deleted = True
            db_caption.deleted_time = int(time.time() * 1000)  # 使用毫秒时间戳

        db.commit()
        return None
    except Exception as e:
        db.rollback()
        print(f"删除描述时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除描述失败: {str(e)}"
        )

# ArtifactCaptionMap API
@app.post("/artifact-caption-maps/", response_model=schemas.ArtifactCaptionMap, status_code=status.HTTP_201_CREATED)
def create_artifact_caption_map(map_data: schemas.ArtifactCaptionMapCreate, db: Session = Depends(get_db)):
    # 检查图片是否存在
    db_artifact = db.query(models.Artifact).filter(models.Artifact.id == map_data.artifact_id).first()
    if db_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"图片不存在: {map_data.artifact_id}"
        )

    # 检查描述是否存在
    db_caption = db.query(models.Caption).filter(models.Caption.id == map_data.caption_id).first()
    if db_caption is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"描述不存在: {map_data.caption_id}"
        )

    # 检查映射是否已存在
    existing_map = db.query(models.ArtifactCaptionMap).filter(
        models.ArtifactCaptionMap.artifact_id == map_data.artifact_id,
        models.ArtifactCaptionMap.caption_id == map_data.caption_id
    ).first()

    if existing_map:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"图片 {map_data.artifact_id} 与描述 {map_data.caption_id} 的映射已存在"
        )

    # 创建新映射
    try:
        db_map = models.ArtifactCaptionMap(**map_data.model_dump())
        db.add(db_map)
        db.commit()
        db.refresh(db_map)
        return db_map
    except Exception as e:
        db.rollback()
        print(f"创建映射时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建映射失败: {str(e)}"
        )

@app.get("/artifact-caption-maps/", response_model=List[schemas.ArtifactCaptionMap])
def read_artifact_caption_maps(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    maps = db.query(models.ArtifactCaptionMap).offset(skip).limit(limit).all()
    return maps

@app.get("/artifact-caption-maps/artifact/{artifact_id}", response_model=List[schemas.ArtifactCaptionMap])
def read_maps_by_artifact(artifact_id: UUID, db: Session = Depends(get_db)):
    maps = db.query(models.ArtifactCaptionMap).filter(
        models.ArtifactCaptionMap.artifact_id == artifact_id
    ).all()
    return maps

@app.get("/artifact-caption-maps/caption/{caption_id}", response_model=List[schemas.ArtifactCaptionMap])
def read_maps_by_caption(caption_id: UUID, db: Session = Depends(get_db)):
    maps = db.query(models.ArtifactCaptionMap).filter(
        models.ArtifactCaptionMap.caption_id == caption_id
    ).all()
    return maps

@app.delete("/artifact-caption-maps/{artifact_id}/{caption_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artifact_caption_map(artifact_id: UUID, caption_id: UUID, db: Session = Depends(get_db)):
    db_map = db.query(models.ArtifactCaptionMap).filter(
        models.ArtifactCaptionMap.artifact_id == artifact_id,
        models.ArtifactCaptionMap.caption_id == caption_id
    ).first()

    if db_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"图片 {artifact_id} 与描述 {caption_id} 的映射不存在"
        )

    try:
        db.delete(db_map)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        print(f"删除映射时发生错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除映射失败: {str(e)}"
        )

# 批量创建映射
@app.post("/artifact-caption-maps/batch/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_artifact_caption_maps_batch(maps_data: List[schemas.ArtifactCaptionMapCreate], db: Session = Depends(get_db)):
    created_count = 0
    skipped_count = 0
    errors = []

    for map_data in maps_data:
        try:
            # 检查图片是否存在
            db_artifact = db.query(models.Artifact).filter(models.Artifact.id == map_data.artifact_id).first()
            if db_artifact is None:
                errors.append(f"图片不存在: {map_data.artifact_id}")
                continue

            # 检查描述是否存在
            db_caption = db.query(models.Caption).filter(models.Caption.id == map_data.caption_id).first()
            if db_caption is None:
                errors.append(f"描述不存在: {map_data.caption_id}")
                continue

            # 检查映射是否已存在
            existing_map = db.query(models.ArtifactCaptionMap).filter(
                models.ArtifactCaptionMap.artifact_id == map_data.artifact_id,
                models.ArtifactCaptionMap.caption_id == map_data.caption_id
            ).first()

            if existing_map:
                skipped_count += 1
                continue

            # 创建新映射
            db_map = models.ArtifactCaptionMap(**map_data.model_dump())
            db.add(db_map)
            created_count += 1

        except Exception as e:
            errors.append(f"处理映射 {map_data.artifact_id}-{map_data.caption_id} 时出错: {str(e)}")

    try:
        db.commit()
        return {
            "success": True,
            "created_count": created_count,
            "skipped_count": skipped_count,
            "errors": errors
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量创建映射失败: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)