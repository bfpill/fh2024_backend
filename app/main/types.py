from pydantic import BaseModel
from typing import Optional 
from uuid import uuid4

class Base(BaseModel):
  empty: str

class BusinessData(BaseModel):
    businessName: str
    goals: str
    websiteUrl: str
    index_css: str

class InteractionDto(BaseModel):
    businessId: str
    taskId: str
    nodeId: str
    
class TaskData(BaseModel):
    businessName: str
    goals: str
    component_id: str
    task_id: Optional[str]
    
class TaskNode(BaseModel):
    timeStartTest: str
    timeEndTest: str
    businessName: str
    component_css: str
    parent_node_id: uuid4 
    hits: int
    engagement_total: int
    score: int
    node_id: uuid4
    
    