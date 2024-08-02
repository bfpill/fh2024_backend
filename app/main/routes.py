from collections import defaultdict
from app.main.data_handlers import fetch_business_hist, write_business_hist, increment_interaction_service
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

@router.post('/test/{business_id}/{task_id}/{node_id}')
async def increment_interaction(business_id, task_id, node_id):
    try:
        increment_interaction_service(business_id, task_id, node_id)
        return {"message": "interactions incremented successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
  
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
      

# we need to change updates but yeah
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
def new_search_tree(businessName, task_id): 
    biz_ref = db.collection('businesses').document(businessName)
    task_ref = db.collection('businesses').document(businessName).collection("tasks").document(task_id)
    
    task_data = task_ref.get()
    task_data = task_data.to_dict()
    
    root_node: TaskNode = {
      "timeStartTest": time.time(),
      "timeEndTest": None,
      "businessName": businessName,
      "component_css": extract_component(businessName, task_data["component_id"]),
      "parent_node_id": None,
      "hits": 0, 
      "engagement_total": 0,
      "score": 0, 
      "node_id": 0,
      "children": []
    }
    
    node_ref = db.collection('businesses').document(businessName).collection("tasks").document(task_id).collection("nodes").document(root_node["node_id"])

    node_ref.set(root_node)
    
  # this really is going to be the nitty gritty of making the product good
  # we need to do a directed search . the direction we move in has to be well bounded but also free
  # how free the algorithm is really depends on how large we want our sample size to be
  # for example, if we want to optimize button size, should we first try an extra large and a small size, 
  # then iteratively move inwards? 
  # or should we slowly test larger and larger sizes? 
  
def fork_test(businessName, task_id, node_id):
    db = firestore.client()
    task_ref = db.collection('businesses').document(businessName).collection('tasks').document(task_id)
    nodes_ref = task_ref.collection('nodes')

    nodes = []
    for doc in nodes_ref.stream():
        node = doc.to_dict()
        node['node_id'] = doc.id 
        nodes.append(node)

    fork_node = next((node for node in nodes if node['node_id'] == node_id), None)
    
    b_data = fetch_business_hist(businessName)
    
    previously_tested_components = [node["component_css"] for node in nodes]
        
    if nodes and fork_node: 
        new_components = generate_new_components(businessName, b_data["goals"],
                                                 fork_node["component_css"], previously_tested_components)
        new_nodes = []
        for component_css in new_components: 
            new_node = {
                "timeStartTest": int(time.time()),
                "timeEndTest": None,
                "business": businessName,
                "component_css": component_css,
                "parent_node_id": node_id,
                "hits": 0, 
                "engagement_total": 0,
                "score": 0, 
                "children": []
            }
            new_nodes.append(new_node)


        for i, new_node in enumerate(new_nodes):
            new_doc_ref = nodes_ref.document() 
            new_node['node_id'] = len(nodes) + i
            new_doc_ref.set(new_node)

        fork_node_ref = nodes_ref.document(node_id)
        fork_node_ref.update({
            "children": firestore.ArrayUnion([node['node_id'] for node in new_nodes])
        })

        return new_nodes
    else:
        return None



async def generate_new_components(goal, parent_node_css, previously_tested_components):
  
  # dummy prompt for now
  # later we need to integrate history
  json_structure = {"css": [
    ".className: version 1",
    ".className: version 2",
    "...",
    ".className: versionN",
    ]}

  num_to_gen = 5
  changeableVars = "Color, Size"
  
  prompt = f'''Please generate {num_to_gen} components that are similar to {parent_node_css}.
  Return the css in a JSON object in the format: 
    {str(json_structure)}
  Here is the current css: 
    {str(parent_node_css)}
  Please only change these variables: 
    {changeableVars}
  Ensure that you do not make something that is similar to any of: 
    {str(changeableVars)}
  '''
  
  completion = await client.chat.completions.create(
    response_format={ "type": "json_object" },
    messages=[{ 
      "role": "system", 
      "content": prompt 
    }], 
    model="gpt-4-0125-preview",
  )

  return completion

  
@router.post('/start_ab_test')
async def start_ab_test(task_info: ABTestInfo):
  businessName = task_info["businessName"]
  # decide what test to do 
  b_data = fetch_business_hist(businessName)
  new_search_tree(businessName, task_info)
  

# dont know if we still need this
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
  
  