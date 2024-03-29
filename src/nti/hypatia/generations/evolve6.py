#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generation 6.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 6

from zope import component

from zope.component.hooks import site
from zope.component.hooks import setHooks

from nti.contentsearch.constants import createdTime_
from nti.contentsearch.constants import lastModified_

from nti.hypatia.interfaces import ISearchCatalog

def do_evolve(context):
	setHooks()
	conn = context.connection
	root = conn.root()
	ds_folder = root['nti.dataserver']

	lsm = ds_folder.getSiteManager()

	with site(ds_folder):
		assert	component.getSiteManager() == ds_folder.getSiteManager(), \
				"Hooks not installed?"

		catalog = lsm.getUtility(provided=ISearchCatalog)
		if createdTime_ in catalog:
			del catalog[createdTime_]

		if lastModified_ in catalog:
			del catalog[lastModified_]

		logger.info('Hypatia evolution %s done', generation)

def evolve(context):
	"""
	Evolve to generation 6 by removing time indices
	"""
	do_evolve(context)
