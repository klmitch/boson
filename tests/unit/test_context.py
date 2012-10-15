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

import mock

from boson import context

import tests


class GenerateRequestIdTestCase(tests.TestCase):
    @mock.patch('uuid.uuid4',
                return_value='9bb4060a-3a1d-49e0-8c9b-b6f16b430cac')
    def test_generate_request_id(self, _mock_uuid4):
        result = context.generate_request_id()

        self.assertEqual(result, 'req-9bb4060a-3a1d-49e0-8c9b-b6f16b430cac')
