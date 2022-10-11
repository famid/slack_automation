import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

SLACK_SIGNING_SECRET = os.environ['SIGNING_SECRET']
SLACK_AUTH_TOKEN = os.environ['SLACK_TOKEN']
