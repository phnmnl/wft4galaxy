#!/usr/bin/env python
from __future__ import print_function

import os as _os
import sys as _sys
import json as _json
import logging as _logging
import argparse as _argparse

from bioblend import ConnectionError
from bioblend.galaxy import GalaxyInstance as _GalaxyInstance

# create a module level logger
_logger = _logging.getLogger("UserManager")


class _CustomFormatter(_argparse.RawTextHelpFormatter):
    """ Customize settings of the default RawTextHelpFormatter """

    def __init__(self, prog, indent_increment=2, max_help_position=40, width=None):
        super(_CustomFormatter, self).__init__(prog, indent_increment, max_help_position, width)


def _make_parser():
    parser = _argparse.ArgumentParser(add_help=True, formatter_class=_CustomFormatter,
                                      description="Create a new Galaxy user programmatically.")
    parser.add_argument('--server', help='Galaxy Server URL', default=_os.environ["GALAXY_URL"])
    parser.add_argument('--api-key', help='Galaxy Admin\'s API KEY', required=True)
    parser.add_argument('--debug', help='Enable debug messages', action="store_true", default=False)
    parser.add_argument('--file', default=None, help='Set a custom output files (default = "<username>.info")')
    parser.add_argument('username', help='User(name) to add')
    parser.add_argument('password', help='User\'s password')
    parser.add_argument('email', help='User\'s email ')
    parser.add_argument('--with-api-key', action="store_true",
                        default=False, help='Create an API KEY for the new user')
    return parser


class GalaxyException(ConnectionError):
    def __init__(self, e):
        super(GalaxyException, self).__init__(self.get_message(e.message, e.body), e.body, e.status_code)

    @staticmethod
    def get_message(message, body):
        if body:
            return _json.loads(body)["err_msg"]
        return message


class CreateUserException(GalaxyException):
    pass


class CreateApiKeyException(GalaxyException):
    pass


def create_user(galaxy_instance, username, password, user_email):
    try:
        user_info = galaxy_instance.users.create_local_user(username=username, password=password, user_email=user_email)
        if user_info is None or "id" not in user_info:
            raise RuntimeError("Possible issue when creating the user: no user ID ca be found!")
        return user_info
    except ConnectionError as e:
        raise CreateUserException(e)


def create_api_key(galaxy_instance, user_id):
    try:
        return galaxy_instance.users.create_user_apikey(user_id)
    except ConnectionError as e:
        raise CreateApiKeyException(e)


def main():
    # configure logger
    _logging.basicConfig(level=_logging.ERROR, format="%(asctime)s [%(name)s] [%(levelname)+4.5s]  %(message)s")

    try:
        # parse args
        parser = _make_parser()
        options = parser.parse_args(_sys.argv[1:])

        # update log level
        if options.debug:
            _logging.basicConfig(level=_logging.DEBUG)
        _logger.debug("Configuration: %s", options)

        # galaxy instance configuration
        gi = _GalaxyInstance(url=options.server, key=options.api_key)

        # user
        user_info = create_user(gi, options.username, options.password, options.email)

        #
        _logger.info("User created: %s" % user_info)

        # add API KEY if required
        if options.with_api_key:
            api_key = create_api_key(galaxy_instance=gi, user_id=user_info["id"])
            user_info["api-key"] = api_key
            _logger.info("Created API KEY: %s", api_key)

        filename = options.file
        if filename is None:
            filename = user_info["username"] + ".info"
        with open(filename, "w") as out:
            _json.dump(user_info, out, indent=4)

        # write to stdout the "api-key"
        print(user_info["api-key"])

        # return
        _sys.exit(0)

    except Exception as e:
        _logger.error(e)
        if _logger.isEnabledFor(_logging.DEBUG):
            _logger.exception(e)
        _sys.exit(99)


if __name__ == "__main__":
    main()
