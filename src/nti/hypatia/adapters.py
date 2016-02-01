#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from zope.intid.interfaces import IIntIds

from perfmetrics import metricmethod

from hypatia.text.parsetree import ParseError

from nti.common.property import Lazy

from nti.contentprocessing import rank_words

from nti.contentsearch.common import get_ugd_indexable_types

from nti.contentsearch.constants import content_

from nti.contentsearch.discriminators import get_acl
from nti.contentsearch.discriminators import query_object

from nti.contentsearch.interfaces import ISearchQuery
from nti.contentsearch.interfaces import IEntityIndexController

from nti.contentsearch.search_results import get_or_create_search_results
from nti.contentsearch.search_results import get_or_create_suggest_results
from nti.contentsearch.search_results import get_or_create_suggest_and_search_results

from nti.dataserver.authentication import effective_principals

from nti.dataserver.authorization import ACT_READ
from nti.dataserver.authorization_acl import has_permission

from nti.dataserver.contenttypes.forums.interfaces import IHeadlinePost
from nti.dataserver.contenttypes.forums.interfaces import IPublishableTopic

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IReadableShared
from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.hypatia import search_queue
from nti.hypatia import search_catalog
from nti.hypatia import get_usernames_of_dynamic_memberships

from nti.hypatia.catalog import SearchCatalogQuery

from nti.hypatia.interfaces import ISearchQueryParser

@component.adapter(IUser)
@interface.implementer(IEntityIndexController)
class _HypatiaUserIndexController(object):

	def __init__(self, entity):
		self.entity = entity

	@Lazy
	def username(self):
		return self.entity.username

	@Lazy
	def intids(self):
		return component.queryUtility(IIntIds)

	@Lazy
	def memberships(self):
		return get_usernames_of_dynamic_memberships(self.entity)
	
	@Lazy
	def effective_principals(self):
		return effective_principals(self.username, everyone=False, skip_cache=True)
	
	def verify_access(self, obj):
		result = obj.isSharedDirectlyWith(self.entity) \
				 if IReadableShared.providedBy(obj) else False
		if not result:
			to_check = obj
			if IHeadlinePost.providedBy(obj):
				to_check = to_check.__parent__
			if IPublishableTopic.providedBy(to_check):
				result = has_permission(ACT_READ, 
										to_check, 
										self.username, 
										principals=self.effective_principals)
			else:
				acl = set(get_acl(obj, ()))
				result = self.memberships.intersection(acl)
		result = bool(result) and not IDeletedObjectPlaceholder.providedBy(obj)
		return result

	def get_object(self, uid):
		result = query_object(uid, intids=self.intids)
		if result is None:
			logger.debug('Could not find object with id %r' % uid)
			try:
				search_queue().remove(uid)
			except TypeError:
				pass
		elif not self.verify_access(result):
			result = None
		return result

	def index_content(self, data):
		pass

	def update_content(self, data):
		pass

	def delete_content(self, data):
		pass

	@metricmethod
	def do_search(self, query, results):
		query = ISearchQuery(query)
		if query.is_empty:
			return results

		searchOn = set(query.searchOn or ())
		if searchOn and not searchOn.intersection(get_ugd_indexable_types()):
			return results

		# parse catalog
		parser = component.getUtility(ISearchQueryParser, name=query.language)
		parsed_query = parser.parse(query, self.entity)

		cq = SearchCatalogQuery(search_catalog(), query)
		try:
			_, sequence = cq.query(parsed_query)
		except ParseError:
			# If we failed to parse the query text return an empty set
			logger.exception("Error parsing search query '%s'", query)
			sequence = {}

		# get docs from db
		for docid, score in sequence.items():
			obj = self.get_object(docid)
			if obj is not None:
				results.add(obj, score)
		return results

	def search(self, query, store=None, **kwargs):
		query = ISearchQuery(query)
		store = get_or_create_search_results(query, store)
		return self.do_search(query, store)

	def suggest(self, query, store=None, **kwargs):
		query = ISearchQuery(query)
		results = get_or_create_suggest_results(query, store)
		if query.is_empty:
			return results

		threshold = query.threshold
		prefix = query.prefix or len(query.term)
		textfield = search_catalog()[content_]  # lexicon is shared

		words = textfield.lexicon.get_similiar_words(term=query.term,
												  	 threshold=threshold,
												 	 common_length=prefix)
		results.add([t[0] for t in words])
		return results

	def suggest_and_search(self, query, store=None, **kwargs):
		query = ISearchQuery(query)
		store = get_or_create_suggest_and_search_results(query, store)
		if ' ' in query.term or query.IsPrefixSearch or query.IsPhraseSearch:
			results = self.do_search(query, store)
		else:
			suggest_results = self.suggest(query)
			suggestions = suggest_results.Suggestions
			if suggestions:
				suggestions = rank_words(query.term, suggestions)
				query.term = suggestions[0]
			results = self.do_search(query, store)
		return results
