#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
hypatia field index

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from BTrees.Length import Length

from hypatia import RangeValue
from hypatia.field import _marker
from hypatia.field import FieldIndex

from nti.zodb.containers import time_to_64bit_int

from .interfaces import ISearchTimeFieldIndex

@interface.implementer(ISearchTimeFieldIndex)
class SearchTimeFieldIndex(FieldIndex):

	def reset(self):
		self._num_docs = Length(0)
		# The forward index maps indexed values to a sequence of docids
		self._fwd_index = self.family.IO.BTree()
		# The reverse index maps a docid to its index value
		# use a II tree since we are storing time as ints
		self._rev_index = self.family.II.LLBTree()
		self._not_indexed = self.family.II.TreeSet()

	def index_doc(self, docid, value):
		value = self.discriminate(value, _marker)
		__traceback_info__ = (docid, value)
		if value is _marker:
			if not (docid in self._not_indexed):
				# unindex the previous value
				self.unindex_doc(docid)
				# Store docid in set of unindexed docids
				self._not_indexed.add(docid)
			return None

		if docid in self._not_indexed:
			# Remove from set of unindexed docs if it was in there.
			self._not_indexed.remove(docid)

		rev_index = self._rev_index
		if docid in rev_index:
			if docid in self._fwd_index.get(value, ()):
				# no need to index the doc, its already up to date
				return
			# unindex doc if present
			self.unindex_doc(docid)

		# Insert into forward index.
		s = self._fwd_index.get(value)
		if s is None:
			s = self.family.II.TreeSet()
			self._fwd_index[value] = s
		s.insert(docid)

		# increment doc count
		self._num_docs.change(1)

		# Insert into reverse index.
		rev_index[docid] = value

	def docids(self):
		not_indexed = self.not_indexed()
		indexed = self.indexed()
		if len(not_indexed) == 0:
			return self.family.II.Set(indexed)
		elif len(indexed) == 0:
			return not_indexed
		indexed = self.family.II.Set(indexed)
		return self.family.II.union(not_indexed, indexed)

	def search(self, queries, operator='or'):
		sets = []
		for q in queries:
			if isinstance(q, RangeValue):
				q = q.as_tuple()
			else:
				q = (q, q)
			values = self._fwd_index.values(*q)
			s = self.family.II.multiunion(values)
			sets.append(s)

		result = None

		if len(sets) == 1:
			result = sets[0]
		elif operator == 'and':
			for _, s in sorted([(len(x), x) for x in sets]):
				result = self.family.II.intersection(s, result)
		else:
			result = self.family.II.multiunion(sets)

		return result

	def apply_intersect(self, query, docids):
		result = self.apply(query)
		if docids is None:
			return result
		return self.family.II.weightedIntersection(result, docids)[1]

	def _negate(self, apply_func, *args, **kw):
		positive = apply_func(*args, **kw)
		all_docids = self.docids()
		if len(positive) == 0:
			return all_docids
		return self.family.II.difference(all_docids, positive)

	def discriminate(self, obj, default):
		value = super(SearchTimeFieldIndex, self).discriminate(obj, default)
		return self.to_int(value)

	def applyEq(self, value):
		return super(SearchTimeFieldIndex, self).applyEq(self.to_int(value))

	def eq(self, value):
		return super(SearchTimeFieldIndex, self).eq(self.to_int(value))

	def noteq(self, value):
		return super(SearchTimeFieldIndex, self).noteq(self.to_int(value))

	def applyGe(self, min_value):
		return super(SearchTimeFieldIndex, self).applyGe(self.to_int(min_value))

	def ge(self, value):
		return super(SearchTimeFieldIndex, self).ge(self.to_int(value))

	def applyLe(self, max_value):
		return super(SearchTimeFieldIndex, self).applyLe(self.to_int(max_value))

	def le(self, value):
		return super(SearchTimeFieldIndex, self).le(self.to_int(value))

	def applyGt(self, min_value):
		return super(SearchTimeFieldIndex, self).applyGt(self.to_int(min_value))

	def gt(self, value):
		return super(SearchTimeFieldIndex, self).gt(self.to_int(value))

	def applyLt(self, max_value):
		return super(SearchTimeFieldIndex, self).applyLt(self.to_int(max_value))

	def lt(self, value):
		return super(SearchTimeFieldIndex, self).lt(self.to_int(value))

	def applyAny(self, values):
		queries = [self.to_int(v) for v in values]
		return self.search(queries, operator='or')

	def any(self, value):
		return super(SearchTimeFieldIndex, self).any(self.to_int(value))

	def notany(self, value):
		return super(SearchTimeFieldIndex, self).notany(self.to_int(value))

	def applyInRange(self, start, end, excludemin=False, excludemax=False):
		return self.family.II.multiunion(
			self._fwd_index.values(
				self.to_int(start), self.to_int(end),
				excludemin=excludemin, excludemax=excludemax)
		)

	def inrange(self, start, end, excludemin=False, excludemax=False):
		return super(SearchTimeFieldIndex, self).inrange(self.to_int(start),
												  		 self.to_int(end),
												  		 excludemin,
												   		 excludemax)

	def notinrange(self, start, end, excludemin=False, excludemax=False):
		return super(SearchTimeFieldIndex, self).notinrange(self.to_int(start),
												 	  		self.to_int(end),
													  		excludemin,
												 	  		excludemax)
	@classmethod
	def to_int(cls, value):
		if type(value) == float:  # auto-convert
			value = time_to_64bit_int(value)
		return value
