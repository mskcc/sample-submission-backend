import csv
import os
import logging
import time
import datetime
import mysql.connector
import json
import numpy as np
import config
from secret_config import *

logger = logging.getLogger('init-authorized-users')
logging_file_handler = logging.FileHandler('logs/init-autorized-users.log')
logging_stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
logging_file_handler.setFormatter(formatter)
logging_stream_handler.setFormatter(formatter)
logger.addHandler(logging_file_handler)
logger.addHandler(logging_stream_handler)
logger.setLevel(logging.INFO)
current_dir = os.getcwd()

db = mysql.connector.connect(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    passwd=MYSQL_PASSWORD,
    database=MYSQL_DB,
)

dbcursor = db.cursor()

# pull Roslin states via Jira API, finds samples for Roslin-Request, creates
# status records for each Roslin status update and each Sample
def init_authorized_users():
    logger.info("Init user table")
    users = []
    line_count = 0
    insert_statement = 'INSERT IGNORE INTO samplereceiving.users (full_name, username, msk_group, role) VALUES (%s, %s, %s, %s)' 
    logger.info(insert_statement)
    with open('samplereceiving-users.txt') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            if line_count == 0:
                logger.info(f'Column names are {", ".join(row)}')
                line_count = 1 
            else:
                users.append(row)
        logger.info(f'Users to be inserted: {users}')
    try:
        logger.info('Inserting into samplereceiving.users')
        dbcursor.executemany(insert_statement, users)
        db.commit()
    finally:
        dbcursor.close()
        logger.info("DONE")

def parse_displayname(display_name):
    display_data = display_name.split("/")
    if len(display_data) != 2:
        return None
    name_data = display_data[0].split(", ")
    if len(name_data) != 2:
        return None
    return name_data[1] + " " + name_data[0]


if __name__ == '__main__':
    init_authorized_users()
