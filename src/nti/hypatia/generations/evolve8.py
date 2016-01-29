#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generation 8

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 8

from zope import component

from zope.component.hooks import site
from zope.component.hooks import setHooks

from hypatia.text import TextIndex
from hypatia.field import FieldIndex

from nti.hypatia.field import SearchFieldIndex

from nti.hypatia.interfaces import ISearchCatalog

from nti.hypatia.text import SearchTextIndex

def do_evolve(context):
	setHooks()
	conn = context.connection
	root = conn.root()
	ds_folder = root['nti.dataserver']

	lsm = ds_folder.getSiteManager()

	logger.info('Hypatia evolution %s started', generation)

	with site(ds_folder):
		assert	component.getSiteManager() == ds_folder.getSiteManager(), \
				"Hooks not installed?"

		catalog = lsm.getUtility(provided=ISearchCatalog)
		for name, index in list(catalog.items()):
			if isinstance(index, FieldIndex):
				new_index = SearchFieldIndex.createFromFieldIndex(index)
				del catalog[name]
				catalog[name] = new_index
			elif isinstance(index, TextIndex):
				new_index = SearchTextIndex.createFromTextIndex(index)
				del catalog[name]
				catalog[name] = new_index

		logger.info('Hypatia evolution %s done', generation)

def evolve(context):
	"""
	Evolve to generation 8 by recreating field & text indices
	"""
	do_evolve(context)
