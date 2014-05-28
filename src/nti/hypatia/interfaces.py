#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
hypatia interfaces

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from zc.catalogqueue.interfaces import ICatalogQueue

from hypatia import interfaces as hypatia_interfaces
from hypatia.text import interfaces as text_interfaces

from nti.contentsearch import interfaces as search_interfaces

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

class ISearchCatalog(hypatia_interfaces.ICatalog):
	pass

class ISearchCatalogQuery(hypatia_interfaces.ICatalogQuery):
	pass

class ISearchKeywordIndex(interface.Interface):

	def strictEq(query):
		"""
		return the docids that have the exact word(s) in the specfied query
		"""

	def removeWord(word):
		"""
		remove the specfied word from this index
		"""

	def replaceWord(word, replacement):
		"""
		replace the specfied word w/ its replacement provided that the latter is not
		stored
		"""

class ISearchTimeFieldIndex(interface.Interface):
	pass

class ISearchLexicon(text_interfaces.ILexicon):

	def get_similiar_words(term, threshold=0.75, common_length=-1):
		"""
		return a list of similar words based on the levenshtein distance
		"""

class ISearchQueryParser(search_interfaces.ISearchQueryParser):

	def parse(query, user=None):
		"""
		parse the specified query
		"""

class IHypatiaUserIndexController(search_interfaces.IEntityIndexController):
	pass
