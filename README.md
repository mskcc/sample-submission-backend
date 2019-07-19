# IGO Sample Submission Backend

## Setting Up Dev Environment

### Install Dependencies

*Use Virtual Python Environment before installing dependecies.*

- make sure you have python3 and uwsgi installed
- create a .ini file in the project folder's top level (examples at VM /srv/www/uwsgi/vassals)
- create secret_config.js file and alter accordingly (examples at VM /srv/www/dev)

```bash
$ python3 -m venv venv 
$ pip install -r requirements.txt
$ uwsgi sample-submission-backend.ini 
```

If you see "IGO Sample Submission Backend" at http://localhost:9004/ you're all set.
