#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from hypatia.text.interfaces import IPipelineElement

from hypatia.text.lexicon import Lexicon
from hypatia.text.lexicon import Splitter
from hypatia.text.lexicon import CaseNormalizer

from nti.hypatia.interfaces import ISearchLexicon

from nti.hypatia.levenshtein import ratio as levenshtein_ratio

@interface.implementer(IPipelineElement)
class StopWordRemover(object):
	"""
	deprecated pipeline. Stop word removal is handled in
	the nti.contentsearch package
	"""
	def stopwords(self):
		return ()

	def process(self, words):
		return words

@interface.implementer(ISearchLexicon)
class SearchLexicon(Lexicon):

	def get_similiar_words(self, term, threshold=0.75, common_length=-1):
		if common_length > -1:
			prefix = term[:common_length]
			words = self._wids.keys(prefix, prefix + u'\uffff')
		else:
			words = self.words()
		for word in words:
			value = levenshtein_ratio(word, term)
			if value > threshold:
				yield (word, value)

	getSimiliarWords = get_similiar_words

def defaultLexicon():
	result = SearchLexicon(Splitter(), CaseNormalizer(), StopWordRemover())
	return result
