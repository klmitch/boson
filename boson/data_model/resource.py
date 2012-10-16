# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from boson.openstack.common.gettextutils import _


class Resource(object):
    """
    Represent a resource.
    """

    def __init__(self, service, name, params=None):
        """
        Initialize a Resource.

        :param service: The Service object the resource is associated
                        with.
        :param name: The name of the resource, as a string; e.g.,
                     "instances", "vcpus", "images", etc.
        :param params: The names of the parameters necessary to
                       identify the resource.  May be omitted.
        """

        self.service = service
        self.name = name
        self.params = set(params) if params else set()


class SpecificResource(object):
    """
    Represent a single resource.
    """

    def __init__(self, resource, param_data=None):
        """
        Initialize a SpecificResource.

        :param resource: The Resource object.
        :param param_data: The parameter data relevant to this
                           resource.  May be omitted if no parameter
                           data is needed to uniquely identify the
                           resource.
        """

        self.resource = resource

        # Filter the parameter data
        if not param_data:
            param_data = {}
        self.param_data = dict((k, v) for k, v in param_data.items()
                               if k in resource.params)

        # Make sure we got everything
        missing = resource.params - set(self.param_data.keys())
        if missing:
            raise ValueError(_("Missing parameter data fields: %s") %
                             ', '.join(repr(f) for f in sorted(missing)))

        # Build the canonical resource name
        self.name = '%s/%s' % (resource.service.name, resource.name)
        if self.param_data:
            param_items = ['%s=%r' % (k, v) for k, v in
                           sorted(self.param_data.items(),
                                  key=lambda x: x[0])]
            self.name += '/%s' % '/'.join(param_items)

    def __hash__(self):
        """Return a hash value of this resource."""

        return hash(self.name)

    def __eq__(self, other):
        """Compare two resources and return equality."""

        return self.name == other.name

    def __ne__(self, other):
        """Compare two resources and return inequality."""

        return self.name != other.name
