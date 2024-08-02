Whenever we want to deploy to heroku we can sync the pyproject / requirements with this: 

## Install requirements
- [Install poetry](https://python-poetry.org/docs/)
```bash
poetry export -f requirements.txt --dev --output requirements.txt
```

to run for dev: 
```bash
source .venv/bin/activate
uvicorn app.app:app --reload

gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```






