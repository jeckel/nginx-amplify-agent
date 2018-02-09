# -*- coding: utf-8 -*-
import os
import time
import traceback
import pwd
import requests

from amplify.agent.common.context import context
from amplify.agent.common.util.loader import import_class

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"

CONFIG_CACHE = {}


def read(config_name, config_file=None):
    """
    Reads specified config and caches it in CONFIG_CACHE dict

    Each config is a python file which can
    Typical name of config for example: /agent/config/app.py

    :param config_name: str config name
    :param config_file: str config file name
    :return: python object
    """
    if config_name not in CONFIG_CACHE:
        full_module_name = 'amplify.agent.common.config.%s' % config_name
        class_name = '%sConfig' % context.environment.title()
        config_object = import_class('%s.%s' % (full_module_name, class_name))(config_file)
        CONFIG_CACHE[config_name] = config_object

    return CONFIG_CACHE[config_name]


def test(config_file, pid_file, wait_for_cloud=False):
    """
    Checks important parameters and checks connection to the cloud

    :param config_file: str config file
    :param pid_file: str pid file
    :param wait_for_cloud: bool - if True the agent will try to connect to the Cloud once again
    :return:
    """
    print('')

    try:
        # check that config file exists
        if not os.path.isfile(config_file) or not os.access(config_file, os.R_OK):
            print("\033[31mConfig file %s could not be found or opened.\033[0m\n" % config_file)
            print("If you installed the agent from the package you should do the following actions:")
            print("  1. sudo cp /etc/amplify-agent/agent.conf.default /etc/amplify-agent/agent.conf")
            print("  2. sudo chown nginx /etc/amplify-agent/agent.conf")
            print("  3. write your API key in [credentials][api_key]")
            return 1

        # check it can be loaded
        try:
            from amplify.agent.common.context import context
            context.setup(
                app='agent',
                config_file=config_file,
                pid_file=pid_file,
                skip_uuid=True
            )
        except IOError, e:
            if hasattr(e, 'filename'):  # log error
                pass
            else:
                raise e

        # check that it contain needed stuff
        if not context.app_config['cloud']['api_url']:
            print("\033[31mAPI url is not specified in %s\033[0m\n" % config_file)
            print("Write API url https://receiver.amplify.nginx.com:443/1.3 in [cloud][api_url]")
            return 1

        if not context.app_config['credentials']['api_key']:
            print("\033[31mAPI key is not specified in %s\033[0m\n" % config_file)
            print("Write your API key in [credentials][api_key]")
            return 1

        # test logger
        try:
            context.log.info('configtest check')
        except:
            current_user = pwd.getpwuid(os.getuid())[0]
            print("\033[31mCould not write to /var/log/amplify-agent/agent.log\033[0m\n")
            print("Either wrong permissions, or the log directory doesn't exist\n")
            print("The following may help:")
            print("  1. sudo mkdir /var/log/amplify-agent")
            print("  2. sudo touch /var/log/amplify-agent/agent.log")
            print("  3. sudo chown %s /var/log/amplify-agent/agent.log" % current_user)
            return 1

        # try to connect to the cloud
        tries = 0
        while tries <= 3:
            tries += 1

            try:
                context.http_client.post('agent/', {})
            except (requests.HTTPError, requests.ConnectionError) as e:
                api_url = context.app_config['cloud']['api_url']
                print("\033[31mCould not connect to cloud via url %s\033[0m\n" % api_url)

                if e.response and e.response.status_code == 404:
                    api_key = context.app_config['credentials']['api_key']
                    print("\033[31mIt seems like your API key '%s' is wrong. \033[0m\n" % api_key)
                    return 1
                else:
                    if (wait_for_cloud and tries == 1) or wait_for_cloud is False:
                        print("\033[31mIt seems like we have little problems connecting to cloud.\033[0m")
                        print("\033[31mApologies and bear with us. \033[0m\n")

                    if wait_for_cloud and tries < 3:
                        print("\033[31mWe will try to establish a connection once again in a minute.\033[0m\n")

                if wait_for_cloud and tries == 3:
                    print("\033[31mGiving up after three attempts...\033[0m\n")
                    return 1
                elif wait_for_cloud is False:
                    return 1
                else:
                    time.sleep(60)
    except:
        print("\033[31mSomething failed:\033[0m\n")
        print(traceback.format_exc())
        return 1

    print("\033[32mConfig file %s is OK\033[0m" % config_file)
    return 0
