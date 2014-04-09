from fabric.operations import local, run
from fabric import api
import os
from config import configuration

api.env.hosts = ["adi@code4sa.org:2222"]

def setup():
    db_config = configuration["databases"]["wards_2006"]
    local("pip install -r requirements/base.txt") 
    if not os.path.exists("{database}.sql".format(database=db_config["database"])):
        local("wget http://wards.code4sa.org/static/sql/{database}.sql".format(database=db_config["database"]))
    local(
        "cat {database}.sql | psql -h {server} -d {database} -U {user}".format(
            server=config["db_host"], database=config["database"], user=db_config["db_user"]
        )
    )

def setup_web():
    local("pip install -r requirements/web.txt") 

def run_web():
    local("python web.py")

def deploy():
    with api.cd(configuration["environment"]["code_dir"]):
        api.run("git pull origin master")
        api.run("%s install -r %s/requirements/web.txt --quiet" % (configuration["environment"]["pip"], configuration["environment"]["code_dir"]))

        api.sudo("supervisorctl restart wards")

