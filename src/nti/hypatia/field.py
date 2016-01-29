#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.deprecation import deprecated

import BTrees

from persistent import Persistent

from hypatia.field import FieldIndex

from nti.hypatia.interfaces import ISearchFieldIndex

@interface.implementer(ISearchFieldIndex)
class SearchFieldIndex(FieldIndex):

	family = BTrees.family64

	@classmethod
	def createFromFieldIndex(cls, index):
		result = cls(discriminator=index.discriminator,
					 family=index.family)
		# reuse internal fields
		result._num_docs = index._num_docs
		result._fwd_index = index._fwd_index
		result._rev_index = index._rev_index
		result._not_indexed = index._not_indexed
		return result

deprecated('SearchTimeFieldIndex', 'No longer used')
class SearchTimeFieldIndex(Persistent):
	pass
