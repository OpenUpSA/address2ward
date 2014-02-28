from fabric.operations import local, run
from fabric import api
import os
import config

api.env.hosts = ["adi@code4sa.org:2222"]

def setup():
    local("pip install -r requirements/base.txt") 
    if not os.path.exists("{database}.sql".format(database=config.database)):
        local("wget http://wards.code4sa.org/static/sql/{database}.sql".format(database=config.database))
    local(
        "cat {database}.sql | psql -h {server} -d {database} -U {user}".format(
            server=config.host, database=config.database, user=config.user
        )
    )

def setup_web():
    local("pip install -r requirements/web.txt") 

def run_web():
    local("python web.py")

def deploy():
    with api.cd(config.code_dir):
        api.run("git pull origin master")
        api.run("%s install -r %s/requirements/web.txt --quiet" % (config.pip, config.code_dir))

        api.sudo("supervisorctl restart wards")

