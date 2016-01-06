# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from betamax import Betamax, BaseMatcher
from betamax.cassette.util import deserialize_prepared_request


class AwsBodyMatcher(BaseMatcher):
    name = 'aws-body'

    def match(self, request, recorded_request):
        recorded_request = deserialize_prepared_request(recorded_request)
        recorded_body = recorded_request.body.split('&')
        request_body = (request.body or b'').split('&')
        return sorted(request_body) == sorted(recorded_body)


class Botomax(Betamax):
    def __init__(self, boto_resource, cassette_library_dir=None,
                 default_cassette_options={}):

        try:
            session = boto_resource.meta.client._endpoint.http_session
        # if the boto resource is a low-level client we don't have
        # to do digg deeper into the object.
        except AttributeError:
            session = boto_resource._endpoint.http_session

        super(Botomax, self).__init__(
            session=session,
            cassette_library_dir=cassette_library_dir,
            default_cassette_options=default_cassette_options)


Betamax.register_request_matcher(AwsBodyMatcher)
