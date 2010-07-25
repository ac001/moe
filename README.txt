 _ __ ___   ___   ___ 
| '_ ` _ \ / _ \ / _ \
| | | | | | (_) |  __/
|_| |_| |_|\___/ \___|

moe is powered by the tipfy framework
tipfy.org is powered by moe
moe is tipfy.

moe later....

========= Install =========
This project used "zc.buildout" for struct and distibution.



=Bootstrap=
Moe needs to use buildout to get libraries etc
Enter the project/ directory and run the bootstrap

This will create a few directories in the project/ directory
and sets up the "enviroment" ready for "buildout"

cd project/
run bootstrap.py --distribute

==Buildout==
This step will pull all the stuff from online onto your machine
such as genshi, make, werk, etc etc..


./bin/buildout


==Run Moe==
Then run the installation with 

/path/to/google_appengine/dev_appserver.py ./app   





