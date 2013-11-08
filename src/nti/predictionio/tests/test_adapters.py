#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from nti.contentfragments.interfaces import IPlainTextContentFragment

from nti.dataserver.users import User
from nti.dataserver.contenttypes import Note

from nti.predictionio import interfaces as pio_interfaces

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.predictionio.tests import ConfiguringTestBase

from hamcrest import (assert_that, has_length, has_entry, none, is_, is_not)

class TestAdapters(ConfiguringTestBase):

	def _create_user(self, username='nt@nti.com', password='temp001', **kwargs):
		usr = User.create_user(self.ds, username=username, password=password, **kwargs)
		return usr

	@WithMockDSTrans
	def test_entity_adapter(self):
		user = self._create_user("aizen@nt.com",
								 external_value={u'alias':u"traitor",
												 u'realname':'aizen'})

		adapted = pio_interfaces.IProperties(user, None)
		assert_that(adapted, is_not(none()))
		assert_that(adapted, has_length(2))
		assert_that(adapted, has_entry('name', 'aizen'))
		assert_that(adapted, has_entry('alias', 'traitor'))

	@WithMockDSTrans
	def test_note_adapter(self):
		note = Note()
		note.title = IPlainTextContentFragment('Release')
		note.tags = (IPlainTextContentFragment('Bankai'),
					 IPlainTextContentFragment('Shikai'))
		prop = pio_interfaces.IProperties(note, None)
		assert_that(prop, is_not(none()))
		assert_that(prop, has_entry('title', 'Release'))
		types = pio_interfaces.ITypes(note, None)
		assert_that(types, is_not(none()))
		assert_that(types, is_(('note', 'bankai', 'shikai')))

