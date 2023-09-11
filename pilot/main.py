# main.py
from __future__ import print_function, unicode_literals
import builtins
import os

from dotenv import load_dotenv

from helpers.ipc import IPCClient
from const.ipc import MESSAGE_TYPE
from utils.utils import json_serial
load_dotenv()

from helpers.Project import Project

from utils.arguments import get_arguments
from logger.logger import logger
from database.database import database_exists, create_database, tables_exist, create_tables, get_created_apps_with_steps
import const.config

def init():
    # Check if the "euclid" database exists, if not, create it
    if not database_exists():
        create_database()

    # Check if the tables exist, if not, create them
    if not tables_exist():
        create_tables()

    arguments = get_arguments()

    logger.info(f"Starting with args: {arguments}")

    return arguments


        
    
def get_custom_print(args):
    built_in_print = builtins.print

    def print_to_external_process(*args, **kwargs):
        # message = " ".join(map(str, args))
        message = args[0]

        if 'type' not in kwargs:
            kwargs['type'] = 'verbose'
        elif kwargs['type'] == MESSAGE_TYPE['local']:
            local_print(*args, **kwargs)
            return

        ipc_client_instance.send({
            'type': MESSAGE_TYPE[kwargs['type']],
            'content': message,
        })
        if kwargs['type'] == MESSAGE_TYPE['user_input_request']:
            return ipc_client_instance.listen()
        
    def local_print(*args, **kwargs):
        message = " ".join(map(str, args))
        if 'type' in kwargs:
            if kwargs['type'] == MESSAGE_TYPE['info']:
                return
            del kwargs['type']

        built_in_print(message, **kwargs)

    ipc_client_instance = None
    if '--external-log-process-port' in args:
        ipc_client_instance = IPCClient(args['--external-log-process-port'])
        return print_to_external_process, ipc_client_instance
    else:
        return local_print, ipc_client_instance

if __name__ == "__main__":
    args = init()

    builtins.print, ipc_client_instance = get_custom_print(args)
    if '--api-key' in args:
        os.environ["OPENAI_API_KEY"] = args['--api-key']

    if '--root-folder' in args:
        const.config.ROOT_FOLDER = args['--root-folder']

    if '--get-created-apps-with-steps' in args:
        print({ 'db_data': get_created_apps_with_steps() }, type='info')
    else:
        # TODO get checkpoint from database and fill the project with it
        project = Project(args, ipc_client_instance=ipc_client_instance)
        project.start()