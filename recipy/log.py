from pymongo import MongoClient
import wrapt
import os
import datetime
import sys
import getpass
import platform
import sys
try:
    from ConfigParser import SafeConfigParser
except:
    from configparser import SafeConfigParser
from git import Repo


RUN_ID = {}
CONFIG = None
store_diff = True

def get_origin(repo):
    try:
        return repo.remotes.origin.url
    except:
        return None

def option(name):
    return not CONFIG.has_option('ignored metadata', name)

def log_init():
    global RUN_ID, CONFIG

    CONFIG = SafeConfigParser(allow_no_value=True)
    CONFIG.read(['.recipyrc', os.path.expanduser("~/.recipyrc")])


    scriptpath = os.path.realpath(sys.argv[0])

    #Start mongoDB client
    client = MongoClient()

    #Access database named 'test_database'
    db = client.recipyDB

    #Create images collection
    recipies = db.recipies

    # Get env info, etc
    run = {"author": getpass.getuser(),
        "description": "",
        "inputs": [],
        "outputs": [],
        "script": scriptpath,
        "command": sys.executable,
        "environment": [platform.platform(), "python " + sys.version.split('\n')[0]],
        "date": datetime.datetime.utcnow()}

    if option('git'):
        try:
            repo = Repo(scriptpath, search_parent_directories=True)
            run["gitrepo"] = repo.working_dir
            run["gitcommit"] =  repo.head.commit.hexsha
            run["gitorigin"] = get_origin(repo)

            if option('diff'):
                whole_diff = ''
                diffs = repo.index.diff(None, create_patch=True)
                for diff in diffs:
                    whole_diff += "\n\n\n" + diff.diff

                run['diff'] = whole_diff
        except:
            pass

    # Put basics into DB
    RUN_ID = recipies.insert(run)
    print("recipy run inserted, with ID %s" % (RUN_ID))
    client.close()

def log_input(filename, source):
    filename = os.path.abspath(filename)
    print("Input from %s using %s" % (filename, source))
    #Update object in DB

    client = MongoClient()

    #Access database named 'test_database'
    db = client.recipyDB

    #Create images collection
    recipies = db.recipies
    recipies.find_and_modify(query={'_id':RUN_ID}, update={"$push": {'inputs': filename}}, upsert=False, full_response=True)
    client.close()

def log_output(filename, source):
    filename = os.path.abspath(filename)
    print("Output to %s using %s" % (filename, source))
    client = MongoClient()

    #Access database named 'test_database'
    db = client.recipyDB

    #Create images collection
    recipies = db.recipies
    recipies.find_and_modify(query={'_id':RUN_ID}, update={"$push": {'outputs': filename}}, upsert=False, full_response=True)
    client.close()