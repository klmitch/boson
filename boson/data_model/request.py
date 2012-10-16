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


class Request(object):
    """
    Represent a resource reservation request.
    """

    def __init__(self, svc_user, deltas, req_id=None):
        """
        Initialize a Request.

        :param svc_user: The ServiceUser the usage is for.
        :param deltas: A dictionary mapping SpecificResource keys to
                       the reserved delta.
        :param req_id: A unique ID associated with the request.  May
                       be omitted.
        """

        self.svc_user = svc_user
        self.deltas = deltas
        self.req_id = req_id
