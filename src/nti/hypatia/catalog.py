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

from zope.cachedescriptors.property import Lazy

from zope.catalog.interfaces import ICatalog as ZOPE_ICATALOG

import BTrees

from hypatia.catalog import Catalog
from hypatia.catalog import CatalogQuery

from hypatia.text.cosineindex import CosineIndex

from nti.contentsearch.discriminators import get_acl
from nti.contentsearch.discriminators import get_tags
from nti.contentsearch.discriminators import get_creator
from nti.contentsearch.discriminators import get_keywords
from nti.contentsearch.discriminators import get_object_ngrams
from nti.contentsearch.discriminators import get_object_content
from nti.contentsearch.discriminators import get_title_and_ngrams
from nti.contentsearch.discriminators import get_replacement_content
from nti.contentsearch.discriminators import get_type as cs_get_type
from nti.contentsearch.discriminators import get_redaction_explanation_and_ngrams

from nti.dataserver import metadata_index

from nti.hypatia.field import SearchFieldIndex

from nti.hypatia.interfaces import ISearchCatalog
from nti.hypatia.interfaces import ISearchCatalogQuery

from nti.hypatia.keyword import SearchKeywordIndex

from nti.hypatia.lexicon import defaultLexicon

from nti.hypatia.text import SearchTextIndex


@interface.implementer(ISearchCatalog)
class SearchCatalog(Catalog):
	family = BTrees.family64

def get_type(obj, default=None):
	result = cs_get_type(obj, default)
	result = (result,) if result and result is not default else default
	return result

def create_catalog(lexicon=None, ngram_lexicon=None, family=BTrees.family64):
	lexicon = defaultLexicon() if lexicon is None else lexicon
	ngram_lexicon = defaultLexicon() if ngram_lexicon is None else ngram_lexicon

	result = SearchCatalog(family=family)

	result['type'] = SearchKeywordIndex(discriminator=get_type, family=family)

	index = CosineIndex(lexicon=lexicon, family=family)
	result['content'] = \
				SearchTextIndex(lexicon=lexicon,
								index=index,
								discriminator=get_object_content,
								family=family)

	index = CosineIndex(lexicon=ngram_lexicon, family=family)
	result['ngrams'] = \
				SearchTextIndex(lexicon=ngram_lexicon,
								index=index,
								discriminator=get_object_ngrams,
								family=family)

	result['tags'] = SearchKeywordIndex(discriminator=get_tags,
								 	   family=family)

	result['keywords'] = SearchKeywordIndex(discriminator=get_keywords,
									 	   family=family)

	index = CosineIndex(lexicon=lexicon, family=family)
	result['title'] = \
				SearchTextIndex(lexicon=lexicon,
								index=index,
								discriminator=get_title_and_ngrams,
								family=family)

	index = CosineIndex(lexicon=lexicon, family=family)
	result['redactionExplanation'] = \
				SearchTextIndex(lexicon=lexicon,
						  		index=index,
						 		discriminator=get_redaction_explanation_and_ngrams,
						 		family=family)

	index = CosineIndex(lexicon=lexicon, family=family)
	result['replacementContent'] = \
				SearchTextIndex(lexicon=lexicon,
								index=index,
								discriminator=get_replacement_content,
								family=family)

	result['creator'] = SearchFieldIndex(discriminator=get_creator,
								  		 family=family)

	result['acl'] = SearchKeywordIndex(discriminator=get_acl,
									   family=family)

	return result

class _proxy(object):

	__slots__ = ('_seq',)

	def __init__(self, seq):
		self._seq = seq

	def items(self):
		for x in self._seq:
			yield x, 1.0

def to_proxy(source):
	source = _proxy(source) if not hasattr(source, "items") else source
	return source

def to_map(source):
	source = to_proxy(source)
	result = {x:y for x, y in source.items()}
	return result

@interface.implementer(ISearchCatalogQuery)
class SearchCatalogQuery(CatalogQuery):

	family = BTrees.family64

	def __init__(self, catalog, search_query, family=None):
		super(SearchCatalogQuery, self).__init__(catalog, family)
		self.search_query = search_query

	@Lazy
	def metadata(self):
		return component.getUtility(ZOPE_ICATALOG, name=metadata_index.CATALOG_NAME)

	def query_metadata_index(self, index, dateRange, mapped=None):
		mapped = {} if mapped is None else mapped
		# query meta-data index
		endTime = dateRange.endTime
		startTime = dateRange.startTime
		docs = index.apply({'between': (startTime, endTime)})

		# intersect result documents with previous docs
		keys = self.family.IF.LFSet(mapped.iterkeys())
		intersected = self.family.IF.intersection(docs, keys)

		# return new result map (docid, score)
		mapped = {x:mapped[x] for x in intersected} if intersected else {}
		numdocs = len(mapped)
		return numdocs, mapped

	def query_by_time(self, numdocs, result):
		creationTime = self.search_query.creationTime
		modificationTime = self.search_query.modificationTime

		if creationTime is not None or modificationTime is not None:
			# if sort_index is used the sort order is lost
			result = to_map(result)
			if creationTime is not None:
				index = self.metadata[metadata_index.IX_CREATEDTIME]
				numdocs, result = self.query_metadata_index(index, creationTime, result)

			if modificationTime is not None:
				index = self.metadata[metadata_index.IX_LASTMODIFIED]
				numdocs, result = self.query_metadata_index(index, modificationTime, result)
		else:
			result = to_proxy(result)

		return numdocs, result

	def search(self, **query):
		numdocs, result = super(SearchCatalogQuery, self).search(**query)
		numdocs, result = self.query_by_time(numdocs, result)
		return numdocs, result

	def query(self, queryobject, sort_index=None, limit=None, sort_type=None,
			  reverse=False, names=None):
		numdocs, result = super(SearchCatalogQuery, self).query(queryobject=queryobject,
																sort_index=sort_index,
																limit=limit,
																sort_type=sort_type,
																reverse=reverse,
																names=names)
		numdocs, result = self.query_by_time(numdocs, result)
		return numdocs, result
