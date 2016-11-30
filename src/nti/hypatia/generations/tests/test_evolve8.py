#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

# from hamcrest import is_
from hamcrest import is_not
# from hamcrest import has_key
# from hamcrest import assert_that
# from hamcrest import same_instance
# from hamcrest import has_properties
does_not = is_not

import unittest

# from hypatia.text import TextIndex
# from hypatia.field import FieldIndex
# 
# from nti.contentsearch.constants import ngrams_
# from nti.contentsearch.constants import creator_
# 
# from nti.hypatia import search_catalog
# 
# from nti.hypatia.generations import evolve8
# 
# from nti.hypatia.interfaces import ISearchTextIndex
# from nti.hypatia.interfaces import ISearchFieldIndex
# 
# import nti.dataserver.tests.mock_dataserver as mock_dataserver
# from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.hypatia.tests import SharedConfiguringTestLayer

def noop(*args):
	pass

@unittest.SkipTest
class TestEvolve8(unittest.TestCase):

	layer = SharedConfiguringTestLayer

# 	@WithMockDSTrans
# 	def test_evolve8(self):
# 		conn = mock_dataserver.current_transaction
# 
# 		catalog = search_catalog()
# 		old_text = catalog[ngrams_] = TextIndex(noop)
# 		old_field = catalog[creator_] = FieldIndex(noop)
# 
# 		assert_that(catalog, has_key(ngrams_))
# 		assert_that(catalog, has_key(creator_))
# 
# 		class _context(object): pass
# 		context = _context()
# 		context.connection = conn
# 
# 		evolve8.do_evolve(context)
# 
# 		assert_that(catalog, has_key(ngrams_))
# 		assert_that(catalog, has_key(creator_))
# 
# 		assert_that(ISearchTextIndex.providedBy(catalog[ngrams_]), is_(True))
# 		assert_that(ISearchFieldIndex.providedBy(catalog[creator_]), is_(True))
# 
# 		assert_that(catalog[ngrams_],
# 					has_properties("lexicon", same_instance(old_text.lexicon),
# 					 			   "index", same_instance(old_text.index),
# 								   "_not_indexed", same_instance(old_text._not_indexed),
# 								   "discriminator", same_instance(old_text.discriminator)))
# 
# 		assert_that(catalog[creator_],
# 					has_properties("_num_docs", same_instance(old_field._num_docs),
# 								   "_fwd_index", same_instance(old_field._fwd_index),
# 								   "_rev_index", same_instance(old_field._rev_index),
# 								   "_not_indexed", same_instance(old_field._not_indexed),
# 								   "discriminator", same_instance(old_field.discriminator)))
