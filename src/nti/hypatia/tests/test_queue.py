#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property

import unittest

from nti.hypatia.queue import SearchCatalogQueue
from nti.hypatia.queue import SearchCatalogEventQueue

from nti.hypatia.tests import SharedConfiguringTestLayer

class TestQueue(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	def test_constructor_event_queue(self):
		queue = SearchCatalogEventQueue()
		assert_that(queue, has_length(0))

	def test_constructor_queue(self):
		queue = SearchCatalogQueue()
		assert_that(queue, has_length(0))
		assert_that(queue, has_property('buckets', is_(1009)))
		assert_that(queue.eventQueueLength(), is_(0))
		assert_that(queue[100], is_not(none()))
