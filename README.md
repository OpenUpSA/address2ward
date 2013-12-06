Simple script that converts street addresses to South African Wards 

update config.py to suit your settings

Install postgis - this is actually quite a bother - I'm not going to describe how to do it here. See the bottom of this file for the commands that I needed to run on my Ubuntu 13.04 machine.

Setup a postgis user and database:

    > sudo su postgres
    > createuser -P <myuser>
    Enter password for new role: 
    Enter it again: 
    Shall the new role be a superuser? (y/n) n
    Shall the new role be allowed to create databases? (y/n) n
    Shall the new role be allowed to create more new roles? (y/n) n

    > createdb --owner=<myuser> <mydb>
    
Install the postgis extensions

    > psql -d <mydb>
    psql (9.1.10)
    Type "help" for help.

    <mydb>=# CREATE EXTENSION postgis;

    \q

Exit from the postgres environment

    > exit

Here are some other commands that I needed to run to get everything working on my machine:

    export LD_LIBRARY_PATH=/usr/local/lib
    sudo ldconfig
    sudo apt-get install rar
    sudo ln -s /usr/lib/postgresql/9.1/bin/shp2pgsql /usr/local/bin/shp2pgsql
make a virtualenv environment and enter it. Then edit config.py as needed. Finally:
    
    fab setup

Now you're ready to go:

    > python convert.py 
    Enter in an address: 16 main rd, cape town
    Full Address: 16 Main Road, Cape Town 7700, South Africa
    Coords: -33.952173, 18.472284
    Province: Western Cape
    Municipality: City of Cape Town Metropolitan Municipality
    Ward: 19100057

Installation of postgis on Ubuntu 13.04. I had problems installing from the repos so I decided to do it from source instead. Here are the commands I needed. YMMV

    sudo apt-get install postgresql-9.1 postgresql-server-dev-9.1

    cd /tmp/

    # Install GEOS
    wget http://download.osgeo.org/geos/geos-3.4.2.tar.bz2
    tar -jxvf geos-3.4.2.tar.bz2
    cd geos-3.4.2
    ./configure; make; sudo make install

    # Install Proj.4
    wget http://download.osgeo.org/proj/proj-4.8.0.tar.gz
    tar -zxvf proj-4.8.0.tar.gz
    cd proj-4.8.0
    ./configure; make; sudo make install

    # GDAL
    wget http://download.osgeo.org/gdal/1.10.1/gdal-1.10.1.tar.gz
    tar -zxvf gdal-1.10.1.tar.gz
    cd gdal-1.10.1
    ./configure; make; sudo make install

    # Refresh library cache
    sudo ldconfig

    wget http://download.osgeo.org/postgis/source/postgis-2.1.1.tar.gz
    tar -zxvf postgis-2.1.1.tar.gz
    cd postgis-2.1.1
    ./configure; make; sudo make install

