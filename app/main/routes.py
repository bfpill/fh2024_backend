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


@router.get('/test/{business_id}')
def handle_page_request():
  try:
    css_file = '''.home-container {
  min-height: 100vh;
  background-color: #f3f4f6;
  }

  .hero-section {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 5rem 0;
  }'''
  
    css_file = get_css(business_id)
    # map_ref.set({})

  except Exception as e: 
    # logger.error(f"Error retrieving user books: {e}")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
  return css_file

class BusinessData(BaseModel):
    businessName: str
    goals: str
    websiteUrl: str

@router.post('/sign_up')
async def submit_form(data: BusinessData):
    try:
        new_doc_ref = db.collection('businesses').document()
        
        business_data = {
            "name": data.businessName,
            "goals": data.goals,
            "websiteUrl": data.websiteUrl,
            "id": new_doc_ref.id
        }

        new_doc_ref.set(business_data)
        
        return {"message": "Business information successfully added", "businessId": new_doc_ref.id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def get_css(business_id): 
  # we are going to have to spread out the history into multiple tables later and write a 
  # function for getting and combining history into something meaningful
  
  # history_ref = db.collection('histories').document(business_id)
  curr_css_ref = db.collection('live_tests').document(business_id)
  doc = curr_css_ref.get()
  data = doc.to_dict()
  
  if not data: 
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

  return data
  
  