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


class Quota(object):
    """
    Represent a quota.  Binds a resource and authentication data with
    a simple limit.
    """

    def __init__(self, resource, auth_data=None, limit=None):
        """
        Initialize a Quota.

        :param resource: The Resource the limit is for.
        :param auth_data: The authentication and authorization data
                          relevant to service users.  The most
                          specific matching quota is applied to a
                          given user.
        :param limit: The limit to apply.  If ``None``, the usage is
                      unlimited.
        """

        self.resource = resource
        self.limit = limit

        # Filter the authentication/authorization data
        if not auth_data:
            auth_data = {}
        self.auth_data = dict((k, v) for k, v in auth_data.items()
                              if k in resource.service.auth_fields)
