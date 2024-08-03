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


def fetch_business_hist(business_id: str):
    biz_ref = db.collection('businesses').document(business_id)
    doc = biz_ref.get()
    data = doc.to_dict()
    return data
    
    
def write_business_hist(business_id: str, data):
    biz_ref = db.collection('businesses').document(business_id)
    biz_ref.set(data)

def increment_interaction_service(business_id: str, task_id: str, node_id: str, aligned_time: str):
  node_ref = db.collection('businesses').document(business_id).collection('tasks').document(task_id).collection('nodes').document(node_id)

  node = node_ref.get()

  if node.exists:
      data = node.to_dict()
      clicks = data.get('clicks', {})
      
      if aligned_time in clicks:
        # Increment the counts
        clicks[aligned_time] = clicks[aligned_time] + 1
        # Update the document with modified clicks dictionary
        node_ref.update({'clicks': clicks})
      else:
        clicks[aligned_time] = 1
        node_ref.update({'clicks': clicks})
      print("Counts incremented successfully.")
  else:
      print("Document does not exist.")

  node_ref.update({
      "interactions": firestore.Increment(1)
  })
