from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from .. import crud, schemas, models, image_processor
from ..database import get_db
from .utils import get_current_active_user
from typing import List
import os

router = APIRouter()


@router.get("/users/{user_id}/item_ids", response_model=List[int])
def read_user_item_ids(user_id: int, db: Session = Depends(get_db)):
    item_ids = crud.get_user_item_ids(db, user_id=user_id)
    if not item_ids:
        raise HTTPException(status_code=404, detail="No items found for this user")
    return item_ids


@router.post("/users/{user_id}/items/", response_model=schemas.Item)
async def create_item_for_user(
        user_id: int,
        description: str = Form(None),
        current_user: models.User = Depends(get_current_active_user),
        file: UploadFile = UploadFile(...),
        db: Session = Depends(get_db)
):
    try:
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to create item for this user")

        # 创建 ItemCreate 对象
        item = schemas.ItemCreate(description=description)

        # 创建 item
        db_item = crud.create_user_item(db=db, item=item, user_id=user_id)

        # 保存图片
        file_path, file_size = await crud.save_uploaded_image(file, db_item.id)

        # 更新 item 的图片路径和大小
        db_item.origin_img_path = file_path
        db_item.origin_img_size = file_size
        db.commit()
        db.refresh(db_item)

        return db_item
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error processing request: {str(e)}")


@router.post("/process/{item_id}/", response_model=schemas.Item)
def process_image(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    image_path = db_item.origin_img_path

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    try:
        # 处理图像
        result = image_processor.process_image(image_path)
        processed_image_path = result
        processed_image_size = os.path.getsize(processed_image_path)
        print(result)
        updated_item = crud.update_item_image_info(db, item_id, processed_image_path, processed_image_size)
        return updated_item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/{item_id}/{image_type}")
async def get_image(item_id: int, image_type: str, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if image_type == "original":
        image_path = db_item.origin_img_path
    elif image_type == "corrected":
        image_path = db_item.correction_img_path
    else:
        raise HTTPException(status_code=400, detail="Invalid image type")

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(image_path)
