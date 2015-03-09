#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import time

from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import greater_than_or_equal_to

import unittest

from nti.contentsearch.interfaces import ISearchQuery
from nti.contentsearch.search_query import DateTimeRange

from nti.contentfragments.interfaces import IPlainTextContentFragment

from nti.dataserver.users import User
from nti.dataserver.users import Community
from nti.dataserver.contenttypes import Note
from nti.dataserver.contenttypes import Redaction
from nti.dataserver.users import DynamicFriendsList

from nti.externalization.internalization import update_from_external_object

from nti.ntiids.ntiids import make_ntiid

from nti.hypatia.interfaces import IHypatiaUserIndexController

import nti.dataserver.tests.mock_dataserver as mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.hypatia.tests import zanpakuto_commands
from nti.hypatia.tests import SharedConfiguringTestLayer

def _create_user(username='nt@nti.com', password='temp001'):
	ds = mock_dataserver.current_mock_ds
	usr = User.create_user(ds, username=username, password=password)
	return usr

class TestLegacySearch(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	def _create_note(self, msg, owner, containerId=None, title=None, inReplyTo=None):
		note = Note()
		if title:
			note.title = IPlainTextContentFragment(title)
		note.body = [unicode(msg)]
		note.creator = owner
		note.inReplyTo = inReplyTo
		note.containerId = containerId or make_ntiid(nttype='bleach', specific='manga')
		return note

	def _add_notes(self, user=None):
		notes = []
		connection = mock_dataserver.current_transaction
		user = user or _create_user()
		for x in zanpakuto_commands:
			note = self._create_note(x, user.username)
			if connection:
				connection.add(note)
			note = user.addContainedObject(note)
			notes.append(note)
		return notes, user

	def _index_notes(self, user=None):
		notes, user = self._add_notes(user=user)
		return user, notes

	@WithMockDSTrans
	def test_query_notes(self):
		user, _ = self._index_notes()
		rim = IHypatiaUserIndexController(user)

		results = rim.search("shield")
		assert_that(results, has_length(1))

		results = rim.search("*")
		assert_that(results, has_length(0))

		results = rim.search("?")
		assert_that(results, has_length(0))

		hits = rim.search("ra*")
		assert_that(hits, has_length(3))

		hits = rim.search('"%s"' % zanpakuto_commands[0])
		assert_that(hits, has_length(1))

		query = ISearchQuery("shield")
		query.searchOn = ("redaction",)
		results = rim.search(query)
		assert_that(results, has_length(0))

		query = ISearchQuery("shield")
		query.searchOn = ("note",)
		results = rim.search(query)
		assert_that(results, has_length(1))

	@WithMockDSTrans
	def test_suggest(self):
		user, _, = self._index_notes()
		rim = IHypatiaUserIndexController(user)

		hits = rim.suggest("ra")
		assert_that(hits, has_length(greater_than_or_equal_to(4)))

	@WithMockDSTrans
	def test_create_redaction(self):
		username = 'kuchiki@bleach.com'
		user = _create_user(username=username)
		redaction = Redaction()
		redaction.selectedText = u'Fear'
		update_from_external_object(redaction,
				{'replacementContent': u'Ichigo',
				 'redactionExplanation': u'Have overcome it everytime I have been on the verge of death'})
		redaction.creator = username
		redaction.containerId = make_ntiid(nttype='bleach', specific='manga')
		redaction = user.addContainedObject(redaction)

		# search
		rim = IHypatiaUserIndexController(user)

		hits = rim.search("fear")
		assert_that(hits, has_length(1))

		hits = rim.search("death")
		assert_that(hits, has_length(1))

		hits = rim.search("ichigo")
		assert_that(hits, has_length(1))

	@WithMockDSTrans
	def test_note_phrase(self):
		username = 'kuchiki@bleach.com'
		user = _create_user(username=username)
		msg = u"you'll be ready to rumble"
		note = Note()
		note.body = [unicode(msg)]
		note.creator = username
		note.containerId = make_ntiid(nttype='bleach', specific='manga')
		note = user.addContainedObject(note)

		# search
		rim = IHypatiaUserIndexController(user)

		hits = rim.search('"you\'ll be ready"')
		assert_that(hits, has_length(1))

		hits = rim.search('"you will be ready"')
		assert_that(hits, has_length(0))

		hits = rim.search('"Ax+B"')
		assert_that(hits, has_length(0))

	@WithMockDSTrans
	def test_note_math_equation(self):
		username = 'ichigo@bleach.com'
		user = _create_user(username=username)
		msg = u"ax+by = 100"
		note = Note()
		note.body = [unicode(msg)]
		note.creator = username
		note.containerId = make_ntiid(nttype='bleach', specific='manga')
		note = user.addContainedObject(note)

		# search
		rim = IHypatiaUserIndexController(user)

		hits = rim.search('"ax+by"')
		assert_that(hits, has_length(1))

		hits = rim.search('"ax by"')
		assert_that(hits, has_length(1))

	@WithMockDSTrans
	def test_columbia_issue(self):
		username = 'ichigo@bleach.com'
		user = _create_user(username=username)
		note = Note()
		note.body = [unicode('light a candle')]
		note.creator = username
		note.containerId = make_ntiid(nttype='bleach', specific='manga')
		note = user.addContainedObject(note)

		# search
		rim = IHypatiaUserIndexController(user)

		hits = rim.search('"light a candle"')
		assert_that(hits, has_length(1))

		hits = rim.search("light a candle")
		assert_that(hits, has_length(1))

	@WithMockDSTrans
	def test_title_indexing(self):
		username = 'ichigo@bleach.com'
		user = _create_user(username=username)
		note = self._create_note(u'The Asauchi breaks away to reveal Hollow Ichigo.', username,
								 title=u'Zangetsu Gone')
		note = user.addContainedObject(note)

		# search
		rim = IHypatiaUserIndexController(user)

		hits = rim.search('Asauchi')
		assert_that(hits, has_length(1))

		hits = rim.search('Zangetsu')
		assert_that(hits, has_length(1))

	@WithMockDSTrans
	def test_note_share_comm(self):
		ds = mock_dataserver.current_mock_ds
		user_1 = User.create_user(ds, username='nti-1.com', password='temp001')
		user_2 = User.create_user(ds, username='nti-2.com', password='temp001')

		c = Community.create_community(ds, username='Bankai')
		for u in (user_1, user_2):
			u.record_dynamic_membership(c)
			u.follow(c)

		note = Note()
		note.body = [unicode('Hitsugaya and Madarame performing Jinzen')]
		note.creator = 'nti.com'
		note.containerId = make_ntiid(nttype='bleach', specific='manga')
		note.addSharingTarget(c)
		note = user_2.addContainedObject(note)

		# search
		rim = IHypatiaUserIndexController(user_1)
		hits = rim.search('Jinzen')
		assert_that(hits, has_length(1))

		rim = IHypatiaUserIndexController(user_2)
		hits = rim.search('Madarame')
		assert_that(hits, has_length(1))

	@WithMockDSTrans
	def test_same_content_two_comm(self):
		ds = mock_dataserver.current_mock_ds
		user = User.create_user(ds, username='nti.com', password='temp001')

		note = Note()
		note.body = [unicode('Only a few atain both')]
		note.creator = 'nti.com'
		note.containerId = make_ntiid(nttype='bleach', specific='manga')

		comms = []
		for name in ('Bankai', 'Shikai'):
			c = Community.create_community(ds, username=name)
			user.record_dynamic_membership(c)
			user.follow(c)
			comms.append(c)
			note.addSharingTarget(c)
		note = user.addContainedObject(note)

		rim = IHypatiaUserIndexController(user)
		hits = rim.search('atain')
		assert_that(hits, has_length(1))

	@WithMockDSTrans
	def test_note_share_dfl(self):
		ds = mock_dataserver.current_mock_ds
		ichigo = User.create_user(ds, username='ichigo@nti.com', password='temp001')
		aizen = User.create_user(ds, username='aizen@nti.com', password='temp001')
		gin = User.create_user(ds, username='gin@nti.com', password='temp001')

		bleach = DynamicFriendsList(username='bleach')
		bleach.creator = ichigo  # Creator must be set
		ichigo.addContainedObject(bleach)
		bleach.addFriend(aizen)
		bleach.addFriend(gin)

		note = Note()
		note.body = [u'Getsuga Tensho']
		note.creator = 'nti.com'
		note.containerId = make_ntiid(nttype='bleach', specific='manga')
		note.addSharingTarget(bleach)
		note = ichigo.addContainedObject(note)

		rim = IHypatiaUserIndexController(gin)
		hits = rim.search('getsuga')
		assert_that(hits, has_length(1))

		rim = IHypatiaUserIndexController(aizen)
		hits = rim.search('tensho')
		assert_that(hits, has_length(1))

	@WithMockDSTrans
	def test_no_need_2_search(self):
		username = 'ichigo@bleach.com'
		user = _create_user(username=username)
		note = self._create_note(u'Yours is an unforgiving bankai', username,
								 title=u'Rukia')
		note = user.addContainedObject(note)

		# search

		rim = IHypatiaUserIndexController(user)
		query = ISearchQuery("bankai")
		query.searchOn = ['content']
		hits = rim.search(query)
		assert_that(hits, has_length(0))

		query = ISearchQuery("bankai")
		query.searchOn = ['note']
		hits = rim.search(query)
		assert_that(hits, has_length(1))

	@WithMockDSTrans
	def test_date_search(self):
		username = 'ichigo@bleach.com'
		user = _create_user(username=username)
		note = self._create_note(u'Yours is an unforgiving bankai', username,
								 title=u'Rukia')
		note = user.addContainedObject(note)

		# search
		now = time.time()
		rim = IHypatiaUserIndexController(user)
		query = ISearchQuery("bankai")
		query.creationTime = DateTimeRange(startTime=now + 100, endTime=now + 1000)
		hits = rim.search(query)
		assert_that(hits, has_length(0))

		query = ISearchQuery("bankai")
		query.creationTime = DateTimeRange(startTime=now - 1000, endTime=now + 1000)
		hits = rim.search(query)
		assert_that(hits, has_length(1))
		
		query = ISearchQuery("notinquery")
		query.creationTime = DateTimeRange(startTime=now - 1000, endTime=now + 1000)
		hits = rim.search(query)
		assert_that(hits, has_length(0))

	@WithMockDSTrans
	def test_inReplyTo(self):
		username = 'ichigo@bleach.com'
		user = _create_user(username=username)
		note1 = self._create_note(u'ichigo', user, title=u'Bleach')
		note1 = user.addContainedObject(note1)

		note2 = self._create_note(u'shikai', user, title=u'Bleach', inReplyTo=note1)
		note2 = user.addContainedObject(note2)

		note3 = self._create_note(u'bankai', user, title=u'Bleach', inReplyTo=note2)
		note3 = user.addContainedObject(note3)
		
		rim = IHypatiaUserIndexController(user)

		results = rim.search("ichigo")
		assert_that(results, has_length(1))

		results = rim.search("shikai")
		assert_that(results, has_length(1))

		results = rim.search("bankai")
		assert_that(results, has_length(1))
