import subprocess
from time import sleep

def clean_environment(cmd: str) -> None:
    nb_containers_up = int(subprocess.getoutput(cmd))

    if(nb_containers_up > 0):
        print('Stopping containers...')
        subprocess.Popen(['docker-compose', 'down'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    
    while(nb_containers_up > 0):
        nb_containers_up = int(subprocess.getoutput(cmd))

def start_environment(cmd: str) -> None:
    print('Starting containers...')
    subprocess.Popen(['docker-compose', 'up', '-d'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    # check that the output can be a digit
    #output = subprocess.getoutput(cmd)
    #while not output.isdigit():
    #    output = subprocess.getoutput(cmd)

    nb_containers_up = int(subprocess.getoutput(cmd))

    while(nb_containers_up < 5):
        nb_containers_up = int(subprocess.getoutput(cmd))
    
    sleep(30)

def before_scenario(context, scenario):
    tag_start_env_before: str = 'start_env_before'
    if tag_start_env_before in scenario.tags:
        cmd: str = "docker-compose ps | grep 'Up' | wc -l | awk '{print $1}'"

        clean_environment(cmd)
        start_environment(cmd)
        

def after_scenario(context, scenario):
    tag_clean_env_after: str = 'clean_env_after'
    if tag_clean_env_after in scenario.tags:
        cmd: str = "docker-compose ps | grep 'Up' | wc -l | awk '{print $1}'"
        clean_environment(cmd)