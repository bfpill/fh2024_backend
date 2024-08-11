When we want to run in dev: 

* OPEN A NEW SHELL
  *  CD into Backend_FH and then run 'poetry shell'
  *  once you are in the venv then run uvicorn app.app:app --reload 
  *  uvicorn should start on the given addr





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


TODO: 


* We need to bake in some kind of stopping mechanism
* trial sibling-only-eval
  * lots of interesting rule subsets
  * trial longer prompts
  * trial different momentum weights

* trial only working off the best found parent until the siblings beat it... 


* investigate how feasible the vector idea actually is
  * how close are the distances we are getting
  * is there anything beyond noise in embedding these vecs
   * How could we embed these better, ie strip some stuff out


* test a multivariate eval
  * big, blue, and certain font size etc

