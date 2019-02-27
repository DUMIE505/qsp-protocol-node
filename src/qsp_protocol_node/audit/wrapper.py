####################################################################################################
#                                                                                                  #
# (c) 2018 Quantstamp, Inc. All rights reserved.  This content shall not be used, copied,          #
# modified, redistributed, or otherwise disseminated except to the extent expressly authorized by  #
# Quantstamp for credentialed users. This content and its use are governed by the Quantstamp       #
# Demonstration License Terms at <https://s3.amazonaws.com/qsp-protocol-license/LICENSE.txt>.      #
#                                                                                                  #
####################################################################################################

import json
import os
import subprocess

from utils.io import (
    dir_exists,
    file_exists,
    is_executable,
)
from stream_logger import get_logger


class Wrapper:

    @staticmethod
    def __check_for_executable_script(script):
        file_exists(script, throw_exception=True)
        is_executable(script, throw_exception=True)

    def __init__(self, home, analyzer_name, args, storage_dir, timeout_sec, prefetch=True):
        self.__logger = get_logger(self.__class__.__qualname__)
        self.__analyzer_name = analyzer_name

        self.__home = home
        self.__args = args

        if not dir_exists(storage_dir):
            os.makedirs(storage_dir)

        self.__storage_dir = storage_dir
        self.__timeout_sec = timeout_sec

        metadata_script = "{0}/metadata".format(self.home)
        run_script = "{0}/run".format(self.home)
        pull_script = "{0}/pull_analyzer".format(self.home)
        Wrapper.__check_for_executable_script(run_script)
        Wrapper.__check_for_executable_script(metadata_script)
        Wrapper.__check_for_executable_script(pull_script)

        self.__metadata_script = metadata_script
        self.__run_script = run_script
        self.__pull_script = pull_script

        # Prefetch the configured analyzer image. If the prefetching fails,
        # an exception is thrown, the program exits and the auto-restart feature kicks in.
        if prefetch:
            self.__prefetch_image()

    @property
    def analyzer_name(self):
        return self.__analyzer_name

    @property
    def home(self):
        return self.__home

    @property
    def args(self):
        return self.__args

    @property
    def storage_dir(self):
        return self.__storage_dir

    @property
    def timeout_sec(self):
        return self.__timeout_sec

    @classmethod
    def __base_environment(cls, wrapper):
        env_vars = {}
    
        env_vars['STORAGE_DIR'] = wrapper.storage_dir
        env_vars['WRAPPER_HOME'] = wrapper.home
        env_vars['ANALYZER_NAME'] = wrapper.analyzer_name         
        env_vars['ANALYZER_ARGS'] = wrapper.args

        return env_vars

    @classmethod
    def __contract_environment(cls, contract_path, original_file_name):
        env_vars = {}

        contract_file_name = os.path.basename(contract_path)
        env_vars['CONTRACT_PATH'] = contract_path
        env_vars['CONTRACT_FILE_NAME'] = contract_file_name
        env_vars['ORIGINAL_FILE_NAME'] = original_file_name

        return env_vars


    def get_metadata(self, contract_path, request_id, original_file_name):
        metadata = {'name': self.__analyzer_name}
        try:
            env_vars = dict(
                os.environ.copy(),
                **Wrapper.__base_environment(self),
                **Wrapper.__contract_environment(self, contract_path, original_file_name)
            )
            self.__logger.debug(
                "Getting {0}'s metadata as subprocess".format(self.analyzer_name),
                requestId=request_id,
            )

            analyzer = subprocess.run(
                self.__metadata_script,
                env=env_vars,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=self.__timeout_sec,
                cwd=self.__home,
            )

            metadata = json.loads(analyzer.stdout)

        except Exception as inner_error:
            self.__logger.error("Error collecting the metadata from {0}'s wrapper: {1}".format(
                    self.analyzer_name,
                    str(inner_error),
                ),
                requestId=request_id
            )

        return metadata

    def __prefetch_image(self):
        try:
            # No contact is needed, only the wrapper home initialization
            env_vars = dict(
                os.environ.copy(),
                **Wrapper.__base_environment(self)
            )
            self.__logger.debug(
                "Executing {0}'s once script to download the image".format(self.analyzer_name)
            )

            subprocess.run(
                self.__pull_script,
                env=env_vars,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=self.__timeout_sec,
                cwd=self.__home,
            )
        except subprocess.CalledProcessError as inner_error:
            msg = "Downloading image for {0}'s wrapper ended with non-zero status: {1}"
            self.__logger.error(msg.format(self.analyzer_name, str(inner_error)))
            raise inner_error
        except Exception as inner_error:
            self.__logger.error("Error downloading image for {0}'s wrapper: {1}".format(
                    self.analyzer_name,
                    str(inner_error),
                )
            )
            raise inner_error

    def check(self, contract_path, request_id, original_file_name):
        json_report = {}
        try:
            env_vars = dict(
                os.environ.copy(),
                **Wrapper.__base_environment(),
                **Wrapper.__contract_environment(contract_path, original_file_name)
            )
            self.__logger.debug("Invoking {0}'s wrapper as subprocess".format(
                    self.analyzer_name
                ),
                requestId=request_id,
            )

            analyzer = subprocess.run(
                self.__run_script,
                env=env_vars,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=self.__timeout_sec,
                cwd=self.__home,
            )

            self.__logger.debug("Wrapper stdout is: {0}".format(str(analyzer.stdout)),
                                requestId=request_id)
            self.__logger.debug("Wrapper stderr is: {0}".format(str(analyzer.stderr)),
                                requestId=request_id)

            json_report = json.loads(analyzer.stdout)

        except Exception as err:
            self.__logger.error("Error running {0}'s wrapper: {1}".format(
                    self.analyzer_name,
                    str(err),
                ),
                requestId=request_id
            )
            # Cannot produce result. Get this back to the callee.
            raise err

        return json_report
