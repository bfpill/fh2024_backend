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
  
  