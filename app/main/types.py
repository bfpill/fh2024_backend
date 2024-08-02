from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

class Base(BaseModel):
  empty: str

class BusinessData(BaseModel):
    businessName: str
    goals: str
    websiteUrl: str
    cssFile: str

class InteractionDto(BaseModel):
    businessId: str
    taskId: str
    nodeId: str
    
class ABTestInfo(BaseModel):
    businessName: str
    goals: str
    component: str
    
class TaskData(BaseModel):
    businessName: str
    goals: str
    component_id: str
  
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
    
    