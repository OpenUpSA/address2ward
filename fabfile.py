from fabric.operations import local
import os
import config

def setup():
    local("pip install -r requirements.txt") 
    if not os.path.exists("Wards.rar"):
        local("wget http://www.demarcation.org.za/Downloads/Boundary/Wards.rar")

    if not os.path.exists("Wards2011.shp"):
        local("rar x Wards.rar")

    local("shp2pgsql -W latin1 Wards2011 wards > wards.sql".format(database=config.database))
    local(
        "psql -h {server} -d {database} -U {user} -f wards.sql".format(
            server=config.host, database=config.database, user=config.user
        )
    )
