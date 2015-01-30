#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from zc.catalogqueue.interfaces import ICatalogQueue

from hypatia.interfaces import ICatalog
from hypatia.interfaces import ICatalogQuery
from hypatia.text.interfaces import ILexicon

from nti.contentsearch.interfaces import ISearchQueryParser
from nti.contentsearch.interfaces import IEntityIndexController

DEFAULT_HEARTBEAT = 10
DEFAULT_QUEUE_LIMIT = 100

class IIndexReactor(interface.Interface):
	"""
	marker interface for a reactor
	"""

class ISearchCatalogEventQueue(interface.Interface):
	pass

class ISearchCatalogQueue(ICatalogQueue):

	buckets = interface.Attribute("number of event queues")

	def syncQueue():
		"""
		sync the length of this queue with its children event queues
		"""

	def eventQueueLength():
		"""
		return the length of all internal search event queues
		"""

	def __getitem__(idx):
		"""
		return the search event queue(s) for the specified index
		"""

class ISearchCatalog(ICatalog):
	pass

class ISearchCatalogQuery(ICatalogQuery):
	pass

class ISearchKeywordIndex(interface.Interface):

	def get_words(docid):
		"""
		return the words for the specified doc id
		"""

	def strict_eq(query):
		"""
		return the docids that have the exact word(s) in the specfied query
		"""

	def remove_word(word):
		"""
		remove the specfied word from this index
		"""

	def replace_word(word, replacement):
		"""
		replace the specfied word w/ its replacement provided that the latter is not
		stored
		"""

class ISearchFieldIndex(interface.Interface):
	"""
	marker interface for field indices
	"""

class ISearchTextIndex(interface.Interface):
	"""
	marker interface for text indices
	"""
	
class ISearchTimeFieldIndex(interface.Interface):
	pass

class ISearchLexicon(ILexicon):

	def get_similiar_words(term, threshold=0.75, common_length=-1):
		"""
		return a list of similar words based on the levenshtein distance
		"""

class ISearchQueryParser(ISearchQueryParser):

	def parse(query, user=None):
		"""
		parse the specified query
		"""

class ISearchCatalogQueueFactory(interface.Interface):
	"""
	A factory for search queues.
	"""
	
class IHypatiaUserIndexController(IEntityIndexController):
	pass
