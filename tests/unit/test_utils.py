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

import uuid

import mock

from boson import utils

import tests


class SerializeTestCase(tests.TestCase):
    def test_none(self):
        self.assertEqual(utils._serialize(None), 'null')

    def test_true(self):
        self.assertEqual(utils._serialize(True), 'true')

    def test_false(self):
        self.assertEqual(utils._serialize(False), 'false')

    def test_int(self):
        self.assertEqual(utils._serialize(12345), '12345')

    def test_long(self):
        self.assertEqual(utils._serialize(12345L), '12345')

    def test_str(self):
        self.assertEqual(utils._serialize("""spam/%="'spam"""),
                         '"spam%2F%25%3D%22%27spam"')

    def test_error(self):
        self.assertRaises(ValueError, utils._serialize, 3.14)


class DeserializeTestCase(tests.TestCase):
    def test_none(self):
        self.assertEqual(utils._deserialize('nUlL'), None)

    def test_true(self):
        self.assertEqual(utils._deserialize('TrUe'), True)

    def test_false(self):
        self.assertEqual(utils._deserialize('fAlSe'), False)

    def test_int(self):
        self.assertEqual(utils._deserialize('12345'), 12345)

    def test_str(self):
        self.assertEqual(utils._deserialize("'spam%2F%25%3d%22%27spam'"),
                         """spam/%="'spam""")

    def test_error(self):
        self.assertRaises(ValueError, utils._deserialize, '3.14')


class AuthSerializeTestCase(tests.TestCase):
    def test_auth_serialize(self):
        test_data = dict(
            alpha="""alpha/%="'""",
            bravo=54321,
            charlie=None,
            delta=True,
            echo=False,
        )
        exemplar = ("""alpha="alpha%2F%25%3D%22%27"/bravo=54321/"""
                    """charlie=null/delta=true/echo=false""")

        self.assertEqual(utils.auth_serialize(test_data), exemplar)


class AuthDeserializeTestCase(tests.TestCase):
    def test_auth_deserialize(self):
        test_data = ("""alpha="alpha%2F%25%3D%22%27"/bravo=54321/"""
                     """charlie=null/delta=true/echo=false""")
        exemplar = dict(
            alpha="""alpha/%="'""",
            bravo=54321,
            charlie=None,
            delta=True,
            echo=False,
        )

        self.assertEqual(utils.auth_deserialize(test_data), exemplar)


class GenerateUuidTestCase(tests.TestCase):
    @mock.patch.object(uuid, 'uuid4',
                       return_value=uuid.UUID(
                       '9bb4060a-3a1d-49e0-8c9b-b6f16b430cac'))
    def test_generate_uuid(self, _mock_uuid4):
        self.assertEqual(utils.generate_uuid(),
                         '9bb4060a-3a1d-49e0-8c9b-b6f16b430cac')
