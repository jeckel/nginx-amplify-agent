# -*- coding: utf-8 -*-
import os
from shutil import copyfile

from hamcrest import *

from amplify.agent.pipelines.file import FileTail
from test.base import BaseTestCase

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class TailTestCase(BaseTestCase):
    test_log = 'log/something.log'
    test_log_rotated = 'log/something.log.rotated'

    def setup_method(self, method):
        # write something to create file
        super(TailTestCase, self).setup_method(method)
        self.write_log('start')

    def write_log(self, line):
        os.system('echo %s >> %s' % (line, self.test_log))
        """
        with open(self.test_log, 'a+') as f:
            print 'writing "%s" to %s' % (line, f.name)
            f.writelines([line])
        """

    def teardown_method(self, method):
        # remove test log
        for filename in (self.test_log, self.test_log_rotated):
            if os.path.exists(filename):
                os.remove(filename)

        super(TailTestCase, self).teardown_method(method)

    def test_read_new_lines(self):
        tail = FileTail(filename=self.test_log)

        # write messages and read them
        for i in xrange(10):
            line = "this is %s line" % i
            self.write_log(line)
            new_lines = tail.readlines()
            assert_that(new_lines, has_length(1))
            assert_that(new_lines.pop(), equal_to(line))

    def test_rotate(self):
        tail = FileTail(filename=self.test_log)

        # rotate it
        os.rename(self.test_log, self.test_log_rotated)

        # write something in a new one
        self.write_log("from a new file")

        # read tail and get two lines
        new_lines = tail.readlines()
        assert_that(new_lines, has_length(1))
        assert_that(new_lines, equal_to(['from a new file']))

    def test_copytruncate(self):
        tail = FileTail(filename=self.test_log)

        lines = ["line %d" % i for i in range(5)]
        for line in lines:
            self.write_log(line)
        assert_that(tail.readlines(), equal_to(lines))

        # mock copytruncate mechanic
        copyfile(self.test_log, self.test_log_rotated)
        with open(self.test_log, 'w') as file_to_truncate:
            file_to_truncate.truncate()

        next_lines = ["line %d" % i for i in range(5,10)]
        for line in next_lines:
            self.write_log(line)

        # check offset is updated to the beginning
        assert_that(tail.readlines(), equal_to(next_lines))

        # resume normal behavior
        final_lines = ["line %d" % i for i in range(10, 15)]
        for line in final_lines:
            self.write_log(line)
        assert_that(tail.readlines(), equal_to(final_lines))

    def test_lose_changes_while_rotate(self):
        tail = FileTail(filename=self.test_log)

        # write something
        self.write_log("from the old file")

        # rotate it
        os.rename(self.test_log, self.test_log_rotated)

        # write something in a new one
        self.write_log("from a new file")

        # read tail and get two lines
        new_lines = tail.readlines()
        assert_that(new_lines, has_length(1))
        assert_that(new_lines, equal_to(['from a new file']))

    def test_no_new_lines(self):
        # check one new line
        tail = FileTail(filename=self.test_log)
        self.write_log('something')
        new_lines = tail.readlines()
        assert_that(new_lines, has_length(1))

        # check no new lines
        new_lines = tail.readlines()
        assert_that(new_lines, has_length(0))

        # and check again one new line
        tail = FileTail(filename=self.test_log)
        self.write_log('something')
        new_lines = tail.readlines()
        assert_that(new_lines, has_length(1))

    def test_cache_offset(self):
        tail = FileTail(filename=self.test_log)
        self.write_log('something')
        tail.readlines()
        old_offset = tail._offset

        # del tail object
        del tail

        # create new
        tail = FileTail(filename=self.test_log)
        assert_that(tail._offset, equal_to(old_offset))
