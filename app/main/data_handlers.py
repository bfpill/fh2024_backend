from logging import getLogger
from openai import AsyncOpenAI, OpenAI
from app.main.settings import getOpenai
from app.main.types import *

from firebase_admin import firestore

db = firestore.client()
logger = getLogger()
client = getOpenai()

def read_fb(id: str,):
  map_ref = db.collection('test').document(id)
  doc = map_ref.get()
  data = doc.to_dict()
  return data 

def write_fb(id: str, data):
  map_ref = db.collection('test').document(id)
  map_ref.set(data)
  return data 


def fetch_business_hist(businessName: str):
    biz_ref = db.collection('businesses').document(businessName)
    doc = biz_ref.get()
    data = doc.to_dict()
    return data
    
    
def write_business_hist(business_id: str, data):
    biz_ref = db.collection('businesses').document(business_id)
    biz_ref.set(data)
    

def increment_interaction_service(business_id: str, task_id: str, node_id: str):
  node_ref = db.collection('businesses').document(business_id).collection('tasks').document(task_id).collection('nodes').document(node_id)

  if node_ref:
    node_ref.update({
        "interactions": firestore.Increment(1)
    })

