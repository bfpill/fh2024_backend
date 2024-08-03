from openai import AsyncOpenAI
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from openai import AsyncOpenAI


import firebase_admin
from firebase_admin import credentials

load_dotenv()

class Settings(BaseSettings):
  openai_api_key: str = "OPENAI_API_KEY NOT SET"
  master_password: str = "MASTER PASS NOT SET"
  firebase_credentials_base64: str = "FIREBASE CRED NOT SET"
  github_token: str = "GITHUB TOKEN NOT SET"

  production: bool = False
  logger_file: str = 'surv.log'
  temp_files: str = '/tmp/surv/tmp'

  class Config:
    env_file = '.env'
    env_file_encoding = 'utf-8'

settings = Settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)

cred = credentials.Certificate("app/firebase_config/firebase_cred.json")
firebase_admin.initialize_app(cred, {'storageBucket': 'fh2024.appspot.com'})

settings = Settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)


# firebase_credentials = json.loads(firebase_credentials_json)

# cred = credentials.Certificate(firebase_credentials)
# firebase_admin.initialize_app(cred,  {'storageBucket': 'storysearch2.appspot.com'})

# def getFireabseApp():
#   return firebase_

def getOpenai():
  return client

