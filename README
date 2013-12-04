Simple script that converts street addresses to South African Wards 

update config.py to suit your settings

Install postgis - this is actually quite a bother - I'm not going to describe how to do it here:

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

    exit

Exit from the postgres environment

    > exit

make a virtualenv environment and enter it

    fab setup

Now you're ready to go:

    > python convert.py 
    Enter in an address: 16 main rd, cape town
    Full Address: 16 Main Road, Cape Town 7700, South Africa
    Coords: -33.952173, 18.472284
    Province: Western Cape
    Municipality: City of Cape Town Metropolitan Municipality
    Ward: 19100057

