#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
predictionIO app

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.utils.schema import SchemaConfigured
from nti.utils.schema import createDirectFieldProperties

from . import interfaces as pio_interfaces

DEFAULT_URL = 'http://localhost:8000'

@interface.implementer(pio_interfaces.IPredictionIOApp)
class PredictionIOApp(SchemaConfigured):
	createDirectFieldProperties(pio_interfaces.IPredictionIOApp)

	def __str__(self):
		return self.AppKey

	def __repr__(self):
		return "%s(%s,%s)" % (self.__class__.__name__, self.URL, self.AppKey)

	def __eq__(self, other):
		try:
			return self is other or (self.AppKey == other.AppKey)
		except AttributeError:
			return NotImplemented

	def __hash__(self):
		xhash = 47
		xhash ^= hash(self.AppKey)
		return xhash

def create_app(appKey, url=DEFAULT_URL):
	url = url or DEFAULT_URL
	result = PredictionIOApp(AppKey=appKey, URL=url)
	return result

