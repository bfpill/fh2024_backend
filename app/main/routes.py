import json
from app.main.data_handlers import extract_component, fetch_business_hist, round_to_nearest_interval, select_top_k_nodes, write_business_hist, update_clicks_service, update_hits_service, fetch_business_analytics, get_selected_css, fetch_businesses
from fastapi import APIRouter, status, HTTPException, Request
from logging import getLogger
from app.main.settings import Settings
from app.main.types import *
from app.main.settings import getOpenai
from uuid import uuid4
import time
from github import Github, GithubException
import os
from app.main.git import get_branch_sha, get_file_sha, create_branch, create_pull_request

from openai import AsyncOpenAI

from app.main.vector_handlers import create_vector, get_closest_components, predict_next_vector

client = AsyncOpenAI()

from firebase_admin import firestore
db = firestore.client()

router = APIRouter()
logger = getLogger()
client = getOpenai()

# settings = Settings()

@router.get('/businesses')
async def handle_page_request():
  try:
    data = fetch_businesses()
    return data
  except Exception as e: 
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
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
      
      
@router.delete('/task/{business_id}/{task_id}')
async def delete_task(business_id: str, task_id: str):
    try:
        task_ref = db.collection('businesses').document(business_id).collection('tasks').document(task_id)
        
        task_data = task_ref.get()
        print(task_data)
        if task_data:
          task_ref.delete()
          return "deleted successfully"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post('/clicks/{business_id}/{task_id}/{node_id}')
async def update_clicks(business_id, task_id, node_id):
    try:
        timestamp = time.time()
        INTERVAL_MINUTES = 5 # this can be changed depending on what time intervals we want to show on the frontend
        aligned_time = str(int(round_to_nearest_interval(timestamp, INTERVAL_MINUTES)))
        print(aligned_time)
        update_clicks_service(business_id, task_id, node_id, aligned_time)

        return {"message": "interactions incremented successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
      
  
@router.post('/hits/{business_id}/{task_id}/{node_id}')
async def update_hits(business_id, task_id, node_id):
    try:
        update_hits_service(business_id, task_id, node_id)
        return {"message": "Hit registered"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
      
@router.get('/embeds/{business_id}/{task_id}/{node_id}')
async def embed_css(business_id, task_id, node_id):
    try:
        task_ref = db.collection('businesses').document(business_id).collection('tasks').document(task_id)
        node_ref = task_ref.collection('nodes').document(node_id)
        
        node = node_ref.get().to_dict()
        vector = await create_vector(node['component_css'])
        
        print(len(vector))
        node_ref.update({"embed": vector})
        
        return {"message": "Hit registered", "vector": vector}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
  
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = 'bfpill/fh2024'
FILE_NAME = 'index.css' 
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO}/contents/blob/master/{FILE_NAME}'
PATH_TO_FILE = f'./app/{FILE_NAME}'
PATH_ON_GITHUB = f'src/{FILE_NAME}'
COMMIT_MESSAGE = f'{FILE_NAME} added via Darwin #{int(time.time())}'
TARGET_BRANCH = 'darwin'

# Define the endpoint to upload the file
@router.post("/upload")
async def upload_file(request: Request):
    try:
        data = await request.json()
        component_css = get_selected_css(data['business_id'], data['task_id'], data['node_id'])

        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)

        if not get_branch_sha(repo, TARGET_BRANCH):
          create_branch(repo, TARGET_BRANCH)

        file_content = repo.get_contents(PATH_ON_GITHUB)
        file_sha = get_file_sha(repo, PATH_ON_GITHUB, TARGET_BRANCH)

        if file_sha:
          # if file exists
          # then update file
          decoded_content = file_content.decoded_content.decode()
          new_content = decoded_content + "\n" + component_css + "\n"
          print("update")
          repo.update_file(PATH_ON_GITHUB, COMMIT_MESSAGE, new_content, file_sha, branch="darwin")
          print(f"File '{PATH_ON_GITHUB}' updated successfully.")   
        else:
          g = Github(GITHUB_TOKEN)
          repo = g.get_repo(GITHUB_REPO)
          print("create file")
          repo.create_file(PATH_ON_GITHUB, COMMIT_MESSAGE, component_css, branch="darwin")
          print(f"File '{PATH_ON_GITHUB}' created successfully.")  
  
        create_pull_request(repo, TARGET_BRANCH, title="Add AB tested CSS", body="Added new CSS rules for index.css through Darwin")

    except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))

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
    await new_search_tree(businessName, task_info.task_id, current_component)
    return current_component, task_info.component_id
  
  else: 
    print("Biz Doesn't Exist")
  


@router.get('/get_biz_info/{businessName}')
async def get_business_info(businessName: str) -> Dict:
    biz_ref = db.collection('businesses').document(businessName)
    biz_doc = biz_ref.get()

    if not biz_doc.exists:
        raise HTTPException(status_code=404, detail="Business not found")

    biz_data = biz_doc.to_dict()

    tasks_ref = biz_ref.collection('tasks')
    tasks_docs = tasks_ref.stream()

    tasks_data = []

    for task_doc in tasks_docs:
        task_data = task_doc.to_dict()
        task_data['id'] = task_doc.id

        nodes_ref = task_doc.reference.collection('nodes')
        nodes_docs = nodes_ref.stream()

        nodes_data = []

        for node_doc in nodes_docs:
            node_data = node_doc.to_dict()
            node_data['id'] = node_doc.id
            nodes_data.append(node_data)

        task_data['nodes'] = nodes_data
        tasks_data.append(task_data)

    biz_data['tasks'] = tasks_data

    return biz_data 


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
  
  node_id = minimal_hit_node["node_id"] if minimal_hit_node else 0

  print(node_id)
  return index_css, current_task_id, node_id


async def fork_test(businessName, task_id, nodes, fork_node): 
      b_data = fetch_business_hist(businessName)
      negative_examples = [node["component_css"] for node in nodes if node["node_id"] != fork_node["node_id"]]
      
      try: 
        if nodes and fork_node:
            # return a string of class css
            new_components = await generate_new_components(b_data["goals"],
                                                      fork_node["component_css"], negative_examples)
            print("new_comps:", new_components)
            new_component_vectors = await create_vector(new_components)
            print(":sfafa")

            if fork_node["node_id"] != '0':
              vector_sequence = get_vector_sequence(businessName, task_id, fork_node["node_id"])
              print("len", len(vector_sequence))
              next_vector_pred = predict_next_vector(vector_sequence)
              print("got here", len(new_component_vectors), len(new_components))

              closest_components_vectors = get_closest_components(new_components, new_component_vectors, next_vector_pred)

              print("closest:", closest_components_vectors)
              if closest_components_vectors:
                new_components = closest_components_vectors
             
            new_nodes = []
            
            for i, component_css in enumerate(new_components):
                new_node = {
                    "timeStartTest": int(time.time()),
                    "timeEndTest": None,
                    "business": businessName,
                    "component_css": component_css,
                    "parent_node_id": fork_node['node_id'],
                    "hits": 0,
                    "clicks": {},
                    "engagement_total": 0,
                    "click_count": 0,
                    "score": 0,
                    "children": [],
                    "status": 'alive',
                    "node_id": str(len(nodes) + i),
                    "embed": new_component_vectors[i]
                }
                new_nodes.append(new_node)

            task_ref = db.collection('businesses').document(businessName).collection('tasks').document(task_id)
            nodes_ref = task_ref.collection('nodes')
    
            batch = db.batch()
            for new_node in new_nodes:
                new_doc_ref = nodes_ref.document(new_node['node_id'])
                batch.set(new_doc_ref, new_node)

            fork_node_ref = nodes_ref.document(fork_node['node_id'])
            batch.update(fork_node_ref, {
                "children": firestore.ArrayUnion([node['node_id'] for node in new_nodes])
            })

            await batch.commit()

            print(f"Fork test completed for business: {businessName}, task: {task_id}")
            return new_nodes
        else:
            return None
      except Exception as e:
        print("BAD", e)


# we need to implement a tree and eliminate all but top k
async def new_search_tree(businessName, task_id, component_css): 
    task_ref = db.collection('businesses').document(businessName).collection("tasks").document(task_id)
    
    task_data = task_ref.get()
    task_data = task_data.to_dict()
    
    vector = await create_vector(component_css)

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
      "embed": vector
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




# this starts at a child node and builds up the vectors from each node on it's path to the root node
def get_vector_sequence(business_name: str, task_id: str, child_node_id: str) -> List[Any]:
    nodes_ref = db.collection('businesses').document(business_name).collection("tasks").document(task_id).collection("nodes")
    
    sequence = []
    current_node_id = child_node_id

    while True:
        node_doc = nodes_ref.document(current_node_id).get()
        
        if not node_doc:
            raise ValueError(f"Node with ID {current_node_id} does not exist")
        
        node = node_doc.to_dict()
        sequence.append(node["embed"])
        
        if node["node_id"] == '0':
            break
        
        current_node_id = node["parent_node_id"]
    
    return list(reversed(sequence))
    
    
async def generate_new_components(goals, parent_node_css, negative_examples, num_to_gen=6):
    print("Attempting CSS component generation")
    
    json_structure = {"css": [
        ".className: version 1",
        ".className: version 2",
        "...",
        ".className: versionN",
    ]}
    
    changeableVars = "Color, Size"

    prompt = f'''Please generate {num_to_gen} components that are similar to {parent_node_css}.
    Return the css in a JSON object in the format: 
        {str(json_structure)}
    Here is the current css: 
        {str(parent_node_css)}
    Please only change these variables: 
        {changeableVars}
    Ensure that you do not make something that is similar to any of: 
        {str(negative_examples)}
    Keep the classname exactly the same as the original.
    Be as creative as possible with the design while adhering to these guidelines.'''
    
    print("Prompt for CSS component generation:")
    print(prompt)

    
    try:
        completion = await client.chat.completions.create(
            response_format={ "type": "json_object" },
            messages=[{ 
                "role": "system", 
                "content": prompt
            }],
            model="gpt-4-0125-preview",
            temperature=0.75
        )

        # Assuming the completion.choices[0].message.content is a JSON string
        new_components = json.loads(completion.choices[0].message.content)['css']
        return new_components
    except Exception as e:
        print(f"An error occurred during component generation: {e}")


