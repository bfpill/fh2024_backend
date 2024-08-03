from datetime import datetime, timedelta
from logging import getLogger
import cssutils
from fastapi import HTTPException
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
  

def fetch_business_analytics(businessName):
    # Reference to the business document
    print("enters")
    business_ref = db.collection('businesses').document(businessName)
    
    # Get the business document
    business_doc = business_ref.get()
    if business_doc.exists:
        business_data = business_doc.to_dict()
        # print("Business data:", business_data)
    else:
        print("No such business!")
        return

    # Reference to the tasks subcollection
    tasks_ref = business_ref.collection('tasks')
    tasks_docs = tasks_ref.stream()
    
    tasks_data = []
    for task in tasks_docs:
        task_data = task.to_dict()
        task_id = task.id

        # Reference to the nodes subcollection for each task
        nodes_ref = tasks_ref.document(task_id).collection('nodes')
        nodes_docs = nodes_ref.stream()
        
        nodes_data = [node.to_dict() for node in nodes_docs]
        task_data['nodes'] = nodes_data
        
        tasks_data.append(task_data)
    
    business_data['tasks'] = tasks_data
    
    print("Business with tasks and nodes data:")
    # print(business_data['tasks'])
    tasks = business_data['tasks']
    for task in tasks:
       print(task)
    return tasks
    
def write_business_hist(business_id: str, data):
    biz_ref = db.collection('businesses').document(business_id)
    biz_ref.set(data)

def update_clicks_service(business_id: str, task_id: str, node_id: str, aligned_time: str):
  biz_ref = db.collection('businesses').document(business_id)
  node_ref = biz_ref.collection('tasks').document(task_id).collection('nodes').document(node_id)

  node = node_ref.get().to_dict()
  
  print(node)

  if node:
      clicks = node["clicks"]
      
      print(clicks)
      if aligned_time in clicks:
        # Increment the counts
        clicks[aligned_time] += 1
        # Update the document with modified clicks dictionary
        node_ref.update({'clicks': clicks})
        
      else:
        clicks[aligned_time] = 1
        node_ref.update({'clicks': clicks})
      print("Counts incremented successfully.")
  else:
      print("Document does not exist.")

  node_ref.update({
      "click_count": node["click_count"] + 1
  })

def update_hits_service(business_id: str, task_id: str, node_id: str):
  node_ref = db.collection('businesses').document(business_id).collection('tasks').document(task_id).collection('nodes').document(node_id)
  node_ref.update({
      "hits": firestore.Increment(1)
  })
  
  
def select_top_k_nodes(nodes, k):
    winning_nodes = []
    scores = []
    
    for node in nodes:
      score = node['click_count'] / (node['hits'] + 1)
      print("score", score)
      scores.append((score, node))
    
    scores.sort(reverse=True, key=lambda x: x[0])
    winning_nodes = [node for _, node in scores[:k]]
    
    return winning_nodes
  
def round_to_nearest_interval(seconds, interval_minutes):
    dt = datetime.fromtimestamp(seconds)
    # Calculate the number of seconds since the start of the hour
    total_seconds = (dt.minute * 60) + dt.second
    interval_seconds = interval_minutes * 60
    # Round to the nearest interval
    rounded_seconds = (total_seconds + interval_seconds // 2) // interval_seconds * interval_seconds
    rounded_time = dt.replace(minute=0, second=0, microsecond=0) + timedelta(seconds=rounded_seconds)
    # Convert back to timestamp
    return rounded_time.timestamp()
  

def extract_component(css_content, component_id):
 
    sheet = None
    try: 
      # Parse the CSS content
      sheet = cssutils.parseString(css_content)
    
    # the library is stupid and old, it throws random errs on a misparse, but f that
    except Exception as e: 
      pass

    for rule in sheet:
      if rule.type == rule.STYLE_RULE:
        if rule.selectorText == f'.{component_id}' or rule.selectorText == component_id:
            print(rule.selectorText)
            return rule.cssText.strip()
    
    return None
 

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