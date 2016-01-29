#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from hypatia.query import Eq
from hypatia.query import Any
from hypatia.query import Contains

from hypatia.text.parsetree import ParseError

from nti.contentsearch.content_utils import is_covered_by_ngram_computer

from nti.contentsearch.interfaces import ISearchQuery

from nti.contentsearch.constants import acl_
from nti.contentsearch.constants import tags_
from nti.contentsearch.constants import type_
from nti.contentsearch.constants import title_
from nti.contentsearch.constants import creator_
from nti.contentsearch.constants import content_
from nti.contentsearch.constants import keywords_
from nti.contentsearch.constants import replacementContent_
from nti.contentsearch.constants import redactionExplanation_

from nti.hypatia import get_user
from nti.hypatia import search_catalog
from nti.hypatia import get_usernames_of_dynamic_memberships

from nti.hypatia.interfaces import ISearchQueryParser

def can_use_ngram_field(query):
	return is_covered_by_ngram_computer(query.term, query.language)

@interface.implementer(ISearchQueryParser)
class _DefaultQueryParser(object):

	singleton = None

	def __new__(cls, *args, **kwargs):
		if not cls.singleton:
			cls.singleton = super(_DefaultQueryParser, cls).__new__(cls)
		return cls.singleton

	def validate(self, query):
		catalog = search_catalog()
		term = query.term.lower()
		try:
			text_idx = catalog[content_]
			text_idx.parse_query(term)
		except ParseError:
			logger.warn("Could not parse text query '%s'", term)
			term = '"%s"' % term
		return term

	def parse(self, query, user=None):
		query = ISearchQuery(query)
		term = self.validate(query)
		return self._parse(query, user, term)

	def _parse(self, query, user, term=None):
		query = ISearchQuery(query)
		term = query.term.lower() if not term else term

		catalog = search_catalog()
		# type
		if query.searchOn:
			type_query = Any(catalog[type_], [x.lower() for x in query.searchOn])
		else:
			type_query = None

		# tags & keywords
		result = Any(catalog[tags_], [term]) | Any(catalog[keywords_], [term])

		fields = (title_, redactionExplanation_, replacementContent_, content_)

		# CS: 20150819 - Remove ngram searching for performance reasons
		# if query.is_prefix_search or query.is_phrase_search or \
		# 	 not can_use_ngram_field(query):
		# 	fields += (content_,)
		# else:
		# 	fields += (ngrams_,)

		for field in fields:
			result = result | Contains(catalog[field], term)

		creator = query.creator
		if creator:
			result = result & Eq(catalog[creator_], creator)

		if type_query is not None:
			result = result & type_query

		user = get_user(user)
		if user:
			usernames = get_usernames_of_dynamic_memberships(user)
			result = result & Any(catalog[acl_], list(usernames))
		return result
