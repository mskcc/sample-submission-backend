# sample-intake-backend

## Setting Up Development Environment

### Install Dependencies

Use Virtual Python Environment if possible before installing dependecies.

- flask
- requests
- yaml
- uwsgi

```bash
$ pip install flask
$ pip install requests --upgrade
$ pip install pyyaml
$ pip install uwsgi
```

### Update Configuration

Open the `lims_user_config` file, and replace `***` with the correct password.

### Run Server

Run `./dev.sh`, browse to `http://localhost:9003/`.

If you see a message `SampleTron 9000`, then you are all set.
