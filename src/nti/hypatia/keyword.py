#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
hypatia keyword index

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from zope import interface

from hypatia.keyword import KeywordIndex

from .interfaces import ISearchKeywordIndex

@interface.implementer(ISearchKeywordIndex)
class SearchKeywordIndex(KeywordIndex):

	def get_words(self, docid):
		result = ()
		if docid in self._rev_index:
			result = tuple(self._rev_index[docid])
		return result

	def index_doc(self, docid, obj):
		__traceback_info__ = docid, obj
		result = super(SearchKeywordIndex, self).index_doc(docid, obj)
		return result

	def strictEq(self, query):
		if isinstance(query, six.string_types):
			query = [query]

		query = self.normalize(query)
		norm = len(query)

		sets = []
		for word in query:
			docids = self._fwd_index.get(word, self.family.IF.Set())
			sets.append(docids)

		for s in sets:
			for docid in list(s):
				ooset = self._rev_index[docid]
				if len(ooset) != norm:
					s.remove(docid)

		result = self.family.IF.multiunion(sets)
		if result:
			return result
		else:
			return self.family.IF.Set()

	def remove_word(self, word):
		result = []
		docids = self._fwd_index.get(word, self.family.IF.Set())
		for docid in list(docids):
			ooset = self._rev_index[docid]
			if len(ooset) == 1:
				result.append(docid)
				self.unindex_doc(docid)
			else:
				ooset.remove(word)
		return result
