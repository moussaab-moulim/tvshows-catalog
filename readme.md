# Moussaab MOULIM item catalog projoct. (FSND)
this the project for item catalog for the the course full stack nano degree
i choose to make a catalog of tvshows and episodes of each tvshow

this project covers the skills i have learned during the the course
witch are:
- working with crud
- makign a webserver
- working with flask framework
- relational object mapping
- making an api endpoint
- working with external apis
- social media sign in with OAUTH
- securing the website ...


## setup envirement
1. install virtualbox where we will install ubunto to run the programs and also instal the database programm Postgres
    [Link for virtual box](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1)
2. install vagrant to connect to the virtual machine from the host and run your command from it
    [Link for vagrant](https://www.vagrantup.com/)
3. clone this github directory https://github.com/udacity/fullstack-nanodegree-vm . you will need it to install the proper configuration needed to run this project
4. open your terminal change directory to Vagrant directory inside the cloned directory
and run this command
    ```
    vagrant up
    ```
    it will install the virtual machine and python and all dependencies needed as well as Postgres (it will take some time)
you can check the file Vagrantfile inside vagrant directory to see all the commands will be running with the vagrant up
5. after the command finish run to login to the virtual machine
    ```
    vagrant ssh
    ```
    now the vagrant file in your host is shared with the virtual machine too
6. copy this project to your vargant folder
7. change directory to this project directory and run
    ```
    python tvshows.py
    ```
    this commande will create and fill up a database with tvshows and their episodes from the open api "Tvmaze" to startup teh project
8. now run this command to start the server
    ```
    python application.py
    ```


now you are up and running 



**Thank you for reading**