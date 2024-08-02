from collections import defaultdict
from fastapi import APIRouter, Depends, status, HTTPException, Header
from logging import getLogger
from app.main.settings import Settings
from app.main.types import *

from fastapi import BackgroundTasks

from firebase_admin import firestore
db = firestore.client()

router = APIRouter()
logger = getLogger()
# settings = Settings()

@router.get('/test/')
def get_book():
  try:
    css_file = '''.home-container {
  min-height: 100vh;
  background-color: #f3f4f6;
}

.hero-section {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  padding: 5rem 0;
}

.hero-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.hero-title {
  font-size: 2.5rem;
  font-weight: bold;
  color: red;
  margin-bottom: 0.5rem;
}

.hero-subtitle {
  font-size: 1.5rem;
  color: #e2e8f0;
  margin-bottom: 2rem;
}

.hero-button {
  background-color: white;
  font-weight: bold;
  padding: 1rem 2rem;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #4a5568;
  transition: background-color 0.3s;
}

.hero-button:hover {
  background-color: #e2e8f0;
}

.features-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem;
}

.features-title {
  font-size: 2.5rem;
  font-weight: bold;
  text-align: center;
  color: #1a202c;
  margin-bottom: 2rem;
}

.features-container {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
}

.feature-card {
  flex-basis: calc(33.333% - 1rem);
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.feature-title {
  font-size: 1.5rem;
  font-weight: bold;
  color: #1a202c;
  margin-bottom: 1rem;
}

.feature-description {
  color: #4a5568;
}

.footer {
  background-color: #1a202c;
  color: white;
  padding: 2.5rem 0;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-title {
  font-size: 1.5rem;
  font-weight: bold;
}

.footer-copyright {
  margin-top: 0.5rem;
}

.footer-link {
  color: #cbd5e0;
  margin-left: 1rem;
  text-decoration: none;
}

.footer-link:hover {
  color: white;
}

@media (max-width: 768px) {
  .features-container {
    flex-direction: column;
  }

  .feature-card {
    flex-basis: 100%;
  }

  .footer-content {
    flex-direction: column;
    text-align: center;
  }

  .footer-links {
    margin-top: 1rem;
  }

  .footer-link {
    margin: 0 0.5rem;
  }
}
    '''
    
    # map_ref = db.collection('test').document("234")
    # map_ref.set({})

  except Exception as e: 
    # logger.error(f"Error retrieving user books: {e}")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
  return css_file

  #   book_doc_ref =  db.document(f'book_ids/{book_id}')
  #   book_doc = book_doc_ref.get()
   
  #   print(book_doc.to_dict())
  #   if book_doc.exists:
  #       book_data = book_doc.to_dict()
  #       return book_data
  #   else:
  #     raise HTTPException(status_code=404, detail="Book not found")
  # except Exception as e:
  #   logger.error(f"Error retrieving user books: {e}")
  #   raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
  return 0
