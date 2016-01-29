#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generation 2.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 2

from zope import component

from zope.component.hooks import site
from zope.component.hooks import setHooks

from zope.intid.interfaces import IIntIds

from zc import intid as zc_intid

from nti.hypatia import search_queue

from nti.hypatia.utils import all_indexable_objects_iids

def do_evolve(context, reg_intid=True):
	setHooks()
	conn = context.connection
	root = conn.root()
	ds_folder = root['nti.dataserver']

	if reg_intid:
		lsm = ds_folder.getSiteManager()
		ds_intid = lsm.getUtility(provided=IIntIds)
		component.provideUtility(ds_intid, IIntIds)
		component.provideUtility(ds_intid, zc_intid.IIntIds)

	logger.info('Hypatia evolution started')

	with site(ds_folder):
		assert	component.getSiteManager() == ds_folder.getSiteManager(), \
				"Hooks not installed?"

		total = 0
		for iid, _ in all_indexable_objects_iids():
			try:
				search_queue().add(iid)
				total += 1
			except TypeError:
				pass

	logger.info('Hypatia evolution done; %s objects added to search queue' % total)
	return total

def evolve(context):
	"""
	Evolve to generation 2 by adding all objects to index queue
	"""
	do_evolve(context)
