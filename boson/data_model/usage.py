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


class Usage(object):
    """
    Represent a resource usage.  Binds a specific resource and a
    service user with the current usage (including positive
    reservations).
    """

    def __init__(self, spc_resource, svc_user, usage=0, reserved=0):
        """
        Initialize a Usage.

        :param spc_resource: The SpecificResource the usage is for.
        :param svc_user: The ServiceUser the usage is for.
        :param usage: The current amount of the resource which is in
                      use by the user.
        :param reserved: The current amount of the resource which is
                         reserved by the user.
        """

        self.spc_resource = spc_resource
        self.svc_user = svc_user
        self.usage = usage
        self.reserved = reserved
