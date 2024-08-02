from collections import defaultdict
from app.main.data_handlers import fetch_business_hist, write_business_hist
from fastapi import APIRouter, status, HTTPException, Header
from logging import getLogger
from app.main.settings import Settings
from app.main.types import *
from app.main.settings import getOpenai
from uuid import uuid4
import time


from firebase_admin import firestore
db = firestore.client()

router = APIRouter()
logger = getLogger()
client = getOpenai()

# settings = Settings()

@router.get('/test/{business_id}')
def handle_page_request(business_id):
  
  # we need to see if we are in the middle of a test or are going to start a new one
  # so some function for that
  # if we aren't in the middle of one we need to start one
  # we can probably abstract that all away to one function
  try:
    css_file = respond_to_site_hit(business_id)

  except Exception as e: 
    # logger.error(f"Error retrieving user books: {e}")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
  return css_file
  
@router.post('/sign_up')
async def sign_up_business(data: BusinessData):
    try:
        new_doc_ref = db.collection('businesses').document()
        
        business_data = {
            "name": data.businessName,
            "goals": data.goals,
            "websiteUrl": data.websiteUrl,
            "id": new_doc_ref.id, 
            "cssFile": data.cssFile,
        }
        
        new_doc_ref.set(business_data)

        return {"message": "Business information successfully added", "businessId": new_doc_ref.id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
      

def respond_to_site_hit(business_id):

  b_data = fetch_business_hist(business_id)

  ret_css, task_id, node_id = b_data["default_css"], b_data["task_id"], b_data["node_id"]
  
  # no test has been started, do nothing
  if not b_data["current_tests"]:
    return ret_css


  A, B = b_data["current_tests"]["A"], b_data["current_tests"]["B"]

   # this is our default 
   # will give a consitent baseline for now? can be changed later
  
  if A["hit_count"] > b_data["test_size"] and B["hit_count"] > b_data["test_size"]:
    # then we need to start a new test and initialize it
    # ideally this needs to be flagged as we get close to the hit limit for the test so that we 
    # can generate the new AB test components before we actually reach the hit limit. 
    # so we'll have to try and guess which will win a little early and have a couple redundant serves. 
    
    # this should async update the A B test and when it is finished update the DB
    fork_test(business_id)

  
  if A["hit_count"] > B["hit_count"]: 
    b_data["current_tests"]["B"]["hit_count"] += 1
    ret_css = B["css"]
  
  else: 
    b_data["current_tests"]["A"]["hit_count"] += 1
    ret_css = A["css"]
    
  write_business_hist(business_id, b_data)
    
  return ret_css, task_id, node_id



def extract_component(business_id, component_id):
  biz_data = fetch_business_hist(business_id)
  index_css = biz_data["index_css"]
  
  
  import re
  pattern = rf'\.{component_id}\s*{{([^}}]+)}}'
  match = re.search(pattern, index_css, re.DOTALL)
    
  if match:
    css_class = match.group(0)
    return css_class.strip()
  else:
    return None
  

# we need to implement a tree and eliminate all but top k
def new_search_tree(business_id, task_id): 
    biz_ref = db.collection('businesses').document(business_id)
    task_ref = db.collection('businesses').document(business_id).collection("tasks").document(task_id)
    
    task_data = task_ref.get()
    task_data = task_data.to_dict()
    
    parent_node: TaskNode = {
      "timeStartTest": time.time(),
      "timeEndTest": None,
      "business": business_id,
      "component_css": extract_component(business_id, task_data["component_id"]),
      "parent_node_id": None,
      "hits": 0, 
      "engagement_total": 0,
      "score": 0, 
      "node_id": uuid4()
    }
    
    task_ref.set({
      "parent_node": parent_node
    }, merge=True)
  
  
  

def fork_test(business_id):
  b_data = fetch_business_hist(business_id)
  A, B = b_data["current_tests"]["A"], b_data["current_tests"]["B"]
  
  
  # this really is going to be the nitty gritty of making the product good
  # we need to do a directed search . the direction we move in has to be well bounded but also free
  # how free the algorithm is really depends on how large we want our sample size to be
  # for example, if we want to optimize button size, should we first try an extra large and a small size, 
  # then iteratively move inwards? 
  # or should we slowly test larger and larger sizes? 
  
  
  pass



async def generate_new_components(task, node: TaskNode):
  task_history = task
  
  
  
@router.post('/start_ab_test')
async def start_ab_test(task_info: ABTestInfo):
  # decide what test to do 
  b_data = fetch_business_hist(task_info.businessName)
  
  # dummy prompt for now
  # later we need to integrate history
  json_structure = {"css": [
    ".class1: ...",
    ".class2: ...",
    ".class3: ...",
    ]}
  
  prompt = f'''Please change the css for component {task_info.component} 
  so that it is a little more {task_info.goals} and return the css in a JSON object in the format: 
    {str(json_structure)}
  Here is the current css: 
    {str(task_info)}
  '''
  
  
  completion = await client.chat.completions.create(
    response_format={ "type": "json_object" },
    messages=[{ 
      "role": "system", 
      "content": prompt 
    }], 
    model="gpt-4-0125-preview",
  )

  return prompt 



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
  
  