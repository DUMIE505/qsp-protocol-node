####################################################################################################
#                                                                                                  #
# (c) 2018 Quantstamp, Inc. All rights reserved.  This content shall not be used, copied,          #
# modified, redistributed, or otherwise disseminated except to the extent expressly authorized by  #
# Quantstamp for credentialed users. This content and its use are governed by the Quantstamp       #
# Demonstration License Terms at <https://s3.amazonaws.com/qsp-protocol-license/LICENSE.txt>.      #
#                                                                                                  #
####################################################################################################

"""
Tests our assumptions about the database client and SQLite3 engine.
"""
import apsw
import unittest
import yaml

from unittest import mock

from config import config_value
from evt.evt_pool_manager import EventPoolManager
from helpers.resource import resource_uri
from timeout_decorator import timeout
from utils.db import Sqlite3Worker
from utils.io import fetch_file


class TestSqlLite3Worker(unittest.TestCase):
    """
    Tests the functionality of the SQLite worker.
    """

    def setUp(self):
        """
        Sets up fresh database for each test.
        """
        cfg = TestSqlLite3Worker.read_yaml_setup('test_config.yaml')
        file = config_value(cfg, '/dev/evt_db_path')
        self.worker = Sqlite3Worker(file)
        self.worker.execute_script(fetch_file(resource_uri('dropdb.sql')))
        self.worker.execute_script(fetch_file(resource_uri('evt/createdb.sql', is_main=True)))

    def tearDown(self):
        """
        Clears the database after the test.
        """
        self.worker.execute_script(fetch_file(resource_uri('dropdb.sql')))
        self.worker.close()

    @timeout(3, timeout_exception=StopIteration)
    def test_execute_create_script(self):
        """
        Tests that the worker is capable of creating the database and insert items by executing a
        script.
        """
        with mock.patch('utils.db.sql3liteworker.logger') as logger_mock:
            self.assertFalse(logger_mock.error.called)
            result = self.worker.execute("select * from evt_status")
            self.assertEqual(len(result), 5,
                            'We are expecting 5 event type records. There are {0}'.format(len(result)))
            self.assertFalse(logger_mock.error.called)

    @timeout(3, timeout_exception=StopIteration)
    def test_inserting_duplicates_primary_key(self):
        """
        Tests that the worker does not propagate raised exception when two records with the same
        primary key are inserted in the database. Also tests that if such an insert is invoked, the
        existing values remain the same.
        """
        with mock.patch('utils.db.sql3liteworker.logger') as logger_mock:
            self.assertFalse(logger_mock.error.called)
            result = self.worker.execute("select * from evt_status")

            # The result is string if the database is locked (caused by previously failed tests)
            self.assertFalse(isinstance(result, str))
            self.assertFalse(logger_mock.error.called)
            original_value = [x for x in result if x['id'] == 'AS'][0]

        with mock.patch('utils.db.sql3liteworker.logger') as logger_mock:
            # Inserts a repeated primary key
            self.worker.execute("insert into evt_status values ('AS', 'Updated received')")
            result = self.worker.execute("select * from evt_status")

            # The result is string if the database is locked (caused by previously failed tests)
            self.assertFalse(isinstance(result, str))
            self.assertEqual(len(result), 5,
                            'We are expecting 5 event type records. There are {0}'.format(len(result)))
            new_value = [x for x in result if x['id'] == 'AS'][0]
            self.assertEqual(new_value, original_value,
                            "The original value changed after the insert")

            # This should stay at the very end after the worker thread has been merged
            self.worker.close()
            self.assertTrue(logger_mock.error.called)

            args, _ = logger_mock.error.call_args
            self.assertTrue(isinstance(args[3], apsw.ConstraintError))

    @timeout(3, timeout_exception=StopIteration)
    def test_inserting_duplicates_events(self):
        """
        Tests that the worker does not propagate raised exception when two records with the same
        primary key are inserted in the database. Also tests that if such an insert is invoked, the
        existing values remain the same.
        """
        with mock.patch('utils.db.sql3liteworker.logger') as sql3liteworker_logger_mock:
            with mock.patch('evt.evt_pool_manager.logger') as evt_pool_manager_logger_mock:
                self.assertFalse(sql3liteworker_logger_mock.warning.called)

                self.worker.execute_script(
                    fetch_file(resource_uri('evt/add_evt_to_be_assigned.sql', is_main=True)),
                    values=(1, 'x', 'x', 'x', 10, 'x', 12),
                    error_handler=EventPoolManager.insert_error_handler
                )

                self.assertFalse(sql3liteworker_logger_mock.warning.called)
                self.assertFalse(evt_pool_manager_logger_mock.warning.called)

        with mock.patch('utils.db.sql3liteworker.logger') as sql3liteworker_logger_mock:
            with mock.patch('evt.evt_pool_manager.logger') as evt_pool_manager_logger_mock:
                self.worker.execute_script(
                    fetch_file(resource_uri('evt/add_evt_to_be_assigned.sql', is_main=True)),
                    values=(1, 'x', 'x', 'x', 10, 'x', 12),
                    error_handler=EventPoolManager.insert_error_handler
                )
                # Ensure that threads were merged before assertions
                self.worker.close()

                self.assertFalse(sql3liteworker_logger_mock.error.called)
                self.assertFalse(evt_pool_manager_logger_mock.error.called)

                self.assertTrue(evt_pool_manager_logger_mock.warning.called)
                args, _ = evt_pool_manager_logger_mock.warning.call_args
                self.assertTrue(isinstance(args[3], apsw.ConstraintError))

    @timeout(3, timeout_exception=StopIteration)
    def test_wrong_select(self):
        """
        Tests that wrong select returns string and logs an error.
        """
        with mock.patch('utils.db.sql3liteworker.logger') as logger_mock:
            self.assertFalse(logger_mock.warning.called)
            result = self.worker.execute("select * from nonexistent_table")

            # The result is string if the database is locked (caused by previously failed tests)
            self.assertTrue(isinstance(result, str))

            # This should stay at the very end after the worker thread has been merged
            self.worker.close()
            self.assertTrue(logger_mock.error.called)

    @staticmethod
    def read_yaml_setup(config_path):
        test_config = fetch_file(resource_uri(config_path))
        with open(test_config) as yaml_file:
            cfg = yaml.load(yaml_file)

        return cfg


if __name__ == '__main__':
    unittest.main()
