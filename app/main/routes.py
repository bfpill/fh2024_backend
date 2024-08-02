from collections import defaultdict
from fastapi import APIRouter, Depends, status, HTTPException, Header
from logging import getLogger
from app.main.settings import Settings
from app.main.types import *

from fastapi import BackgroundTasks

from firebase_admin import firestore
db = firestore.client()

router = APIRouter()
logger = getLogger()
# settings = Settings()

@router.get('/test/{param}', tags=["Book", "User"])
def get_book(param: str):
  try:
    print("Getting this in the log")
    map_ref = db.collection('test').document("234")
    map_ref.set({})

  except Exception as e: 
    logger.error(f"Error retrieving user books: {e}")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
  return "nutsack"

  #   book_doc_ref =  db.document(f'book_ids/{book_id}')
  #   book_doc = book_doc_ref.get()
   
  #   print(book_doc.to_dict())
  #   if book_doc.exists:
  #       book_data = book_doc.to_dict()
  #       return book_data
  #   else:
  #     raise HTTPException(status_code=404, detail="Book not found")
  # except Exception as e:
  #   logger.error(f"Error retrieving user books: {e}")
  #   raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
  return 0
