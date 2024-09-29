from models import mango_configuration

mango_conf = mango_configuration(
    root_user="admin", # get this value from file=docker_compose_env
    root_pass="admin", # get this value from file=docker_compose_env
    url = "mongodb:27017",
)