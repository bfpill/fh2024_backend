import json
from app.main.data_handlers import extract_component, fetch_business_hist, select_top_k_nodes, write_business_hist, update_clicks_service, update_hits_service, fetch_business_analytics
from fastapi import APIRouter, status, HTTPException
from logging import getLogger
from app.main.settings import Settings
from app.main.types import *
from app.main.settings import getOpenai
from uuid import uuid4
import time

from openai import AsyncOpenAI

client = AsyncOpenAI()

from firebase_admin import firestore
db = firestore.client()

router = APIRouter()
logger = getLogger()
client = getOpenai()

# settings = Settings()

@router.get('/test/{business_id}')
async def handle_page_request(business_id):
  
  # we need to see if we are in the middle of a test or are going to start a new one
  # so some function for that
  # if we aren't in the middle of one we need to start one
  # we can probably abstract that all away to one function
  try:
    css_file, task_id, node_id = await respond_to_site_hit(business_id)

  except Exception as e: 
    # logger.error(f"Error retrieving user books: {e}")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
  print(css_file != None, task_id, node_id)
  return {"css_file": css_file, "task_id": task_id, "node_id":node_id}

@router.get('/analytics/{business_id}')
def get_business_analytics(business_id):
   try:
      tasks = fetch_business_analytics(business_id)
      return tasks
   except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post('/test/{business_id}/{task_id}/{node_id}/clicks')
async def update_clicks(business_id, task_id, node_id):
    try:
        timestamp = time.time()
        INTERVAL_MINUTES = 5 # this can be changed depending on what time intervals we want to show on the frontend
        aligned_time = str(int(round_to_nearest_interval(timestamp, INTERVAL_MINUTES)))
        update_clicks_service(business_id, task_id, node_id, aligned_time)

        return {"message": "interactions incremented successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
      
  
@router.post('/test/{business_id}/{task_id}/{node_id}/hits')
async def update_hits(business_id, task_id, node_id):
    try:
        update_hits_service(business_id, task_id, node_id)
        return {"message": "Hit registered"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
  

@router.post('/sign_up')
async def sign_up_business(data: BusinessData):
    try:
        new_doc_ref = db.collection('businesses').document(data.businessName)
        
        business_data = {
            "name": data.businessName,
            "goals": data.goals,
            "websiteUrl": data.websiteUrl,
            "id": new_doc_ref.id, 
            "index_css": data.index_css,
        }
        
        new_doc_ref.set(business_data)

        return {"message": "Business information successfully added", "businessId": new_doc_ref.id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# we need to change updates but yeah
async def respond_to_site_hit(business_id):
  # hard_coded for now
  test_size = 1
  # we need to count clicks with timestamps

  b_data = fetch_business_hist(business_id)
  print("Biz Id: ", business_id)
  if not b_data: 
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str("Bad Biz Id"))
    
  index_css = b_data["index_css"]
  # no test has been started, do nothing
  if not "current_task_id" in b_data:
    return index_css, None, None
  
  # this is our default 
  # will give a consitent baseline for now? can be changed later
  current_task_id = b_data["current_task_id"]

  print(index_css != None, current_task_id)
  
  task_ref = db.collection('businesses').document(business_id).collection('tasks').document(current_task_id)
  nodes_ref = task_ref.collection('nodes')
  
  minimal_hit_node, minimal_hits = None, float('inf')
  # the check to see if the test is over

  nodes = []
  for doc in nodes_ref.stream():
    node = doc.to_dict()
    print(node)

    if 'status' in node and node['status'] == "dead":
      nodes.append(node)
      continue
    else: 
      node['status'] = 'alive'

    hits = node['hits']
    if hits >= test_size:
      node['status'] = "dead"
      node_ref = task_ref.collection('nodes').document(node['node_id'])
      node_ref.set(node)

    elif hits < minimal_hits:
      minimal_hit_node = node
      
    nodes.append(node)
  
  # then we need to start a new test and initialize it
  # ideally this needs to be flagged as we get close to the hit limit for the test so that we 
  # can generate the new AB test components before we actually reach the hit limit. 
  # so we'll have to try and guess which will win a little early and have a couple redundant serves. 
  # this should async update the A B test and when it is finished update the DB
  if not minimal_hit_node:
    k = 1
    print("k")
    winners = select_top_k_nodes(nodes, k)
    print("winners", winners)

    for node in winners: 
      await fork_test(business_id, current_task_id, nodes, node)
    
  else: 
    index_css += minimal_hit_node["component_css"]

  write_business_hist(business_id, b_data)
  
  node_id = None
  if minimal_hit_node: 
    node_id = minimal_hit_node["node_id"]
    
  print(node_id)
  return index_css, current_task_id, node_id


async def fork_test(businessName, task_id, nodes, fork_node):
    print("fork_node", fork_node)
    
    try:
        b_data = fetch_business_hist(businessName)
        previously_tested_components = [node["component_css"] for node in nodes]
        if nodes and fork_node:
            print("got here")
            new_components = await generate_new_components(b_data["goals"],
                                                    fork_node["component_css"], previously_tested_components)
            new_nodes = []
            for i, component_css in enumerate(new_components):
                print(component_css)
                new_node = {
                    "timeStartTest": int(time.time()),
                    "timeEndTest": None,
                    "business": businessName,
                    "component_css": component_css,
                    "parent_node_id": fork_node['node_id'],
                    "hits": 0,
                    "clicks": [],
                    "engagement_total": 0,
                    "click_count": 0,
                    "score": 0,
                    "children": [],
                    "status": 'alive',
                    "node_id": str(len(previously_tested_components) + i)
                }
                new_nodes.append(new_node)

            task_ref = db.collection('businesses').document(businessName).collection('tasks').document(task_id)
            nodes_ref = task_ref.collection('nodes')
    
            # Use a batch write for efficiency
            batch = db.batch()
            for new_node in new_nodes:
                new_doc_ref = nodes_ref.document(new_node['node_id'])
                batch.set(new_doc_ref, new_node)

            fork_node_ref = nodes_ref.document(fork_node['node_id'])
            batch.update(fork_node_ref, {
                "children": firestore.ArrayUnion([node['node_id'] for node in new_nodes])
            })

            # Commit the batch
            await batch.commit()

            print(f"Fork test completed for business: {businessName}, task: {task_id}")
            return new_nodes
        else:
            return None
    except Exception as e:
        print(f"An error occurred during fork test: {e}")
        return None


# we need to implement a tree and eliminate all but top k
def new_search_tree(businessName, task_id, component_css): 
    task_ref = db.collection('businesses').document(businessName).collection("tasks").document(task_id)
    
    task_data = task_ref.get()
    task_data = task_data.to_dict()

    root_node: TaskNode = {
      "timeStartTest": time.time(),
      "timeEndTest": None,
      "businessName": businessName,
      "component_css": component_css,
      "parent_node_id": None,
      "hits": 0, 
      "clicks": {},
      "score": 0, 
      "node_id": "0",
      "children": [], 
      "status": "alive",
      "click_count": 0,
    }
    
    print(root_node)
    
    biz_ref = db.collection('businesses').document(businessName)
    node_ref = biz_ref.collection("tasks").document(task_id).collection("nodes").document(root_node["node_id"])

    node_ref.set(root_node)
    
  # this really is going to be the nitty gritty of making the product good
  # we need to do a directed search . the direction we move in has to be well bounded but also free
  # how free the algorithm is really depends on how large we want our sample size to be
  # for example, if we want to optimize button size, should we first try an extra large and a small size, 
  # then iteratively move inwards? 
  # or should we slowly test larger and larger sizes? 


async def generate_new_components(goal, parent_node_css, previously_tested_components):
    print("attempting generation")
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
        {str(previously_tested_components)}
    Keep the classname exactly the same as the original.
    '''
    
    print(prompt)

    try:
        completion = await client.chat.completions.create(
            response_format={ "type": "json_object" },
            messages=[{ 
                "role": "system", 
                "content": prompt 
            }],
            model="gpt-4-0125-preview",
        )

        
        # Assuming the completion.choices[0].message.content is a JSON string
        new_components = json.loads(completion.choices[0].message.content)['css']
        return new_components
    except Exception as e:
        print(f"An error occurred during component generation: {e}")
        return []


  
@router.post('/start_ab_test')
async def start_ab_test(task_info: TaskData):
  businessName = task_info.businessName
  # decide what test to do 

  biz_ref = db.collection('businesses').document(businessName)
  biz_data = biz_ref.get().to_dict()

  if biz_data:
    biz_data['current_task_id'] = task_info.task_id
    biz_ref.set(biz_data)

    task_ref = biz_ref.collection('tasks').document(task_info.task_id)
    task_ref.set(task_info.model_dump())
    
    index_css = biz_data["index_css"]
    
      # if not component_id: 
        # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str("No component_id found for task"))
    
    current_component = extract_component(index_css, task_info.component_id)
    new_search_tree(businessName, task_info.task_id, current_component)
    return current_component, task_info.component_id
  
  else: 
    print("Biz Doesn't Exist")
  


  
  