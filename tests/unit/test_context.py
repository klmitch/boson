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
    @mock.patch('boson.utils.generate_uuid',
                return_value='9bb4060a-3a1d-49e0-8c9b-b6f16b430cac')
    def test_generate_request_id(self, _mock_uuid4):
        result = context.generate_request_id()

        self.assertEqual(result, 'req-9bb4060a-3a1d-49e0-8c9b-b6f16b430cac')


class ContextTestCase(tests.TestCase):
    def test_init(self):
        ctx = context.Context('user', 'tenant', roles=['one', 'two'],
                              request_id='request_id', is_admin=True,
                              spam='spam')

        self.assertEqual(ctx.user, 'user')
        self.assertEqual(ctx.tenant, 'tenant')
        self.assertEqual(ctx.roles, ['one', 'two'])
        self.assertEqual(ctx.request_id, 'request_id')
        self.assertEqual(ctx.is_admin, True)
        self.assertEqual(ctx.session, None)

    @mock.patch.object(context, 'generate_request_id',
                       return_value='request_id')
    def test_init_bare(self, _mock_generate_request_id):
        ctx = context.Context('user', 'tenant')

        self.assertEqual(ctx.user, 'user')
        self.assertEqual(ctx.tenant, 'tenant')
        self.assertEqual(ctx.roles, [])
        self.assertEqual(ctx.request_id, 'request_id')
        self.assertEqual(ctx.is_admin, False)
        self.assertEqual(ctx.session, None)

    def test_init_admin(self):
        ctx = context.Context('user', 'tenant', roles=['one', 'aDmIn', 'two'],
                              request_id='request_id')

        self.assertEqual(ctx.user, 'user')
        self.assertEqual(ctx.tenant, 'tenant')
        self.assertEqual(ctx.roles, ['one', 'aDmIn', 'two'])
        self.assertEqual(ctx.request_id, 'request_id')
        self.assertEqual(ctx.is_admin, True)
        self.assertEqual(ctx.session, None)

    @mock.patch.object(context.Context, '__init__', return_value=None)
    def test_from_dict(self, mock_init):
        result = context.Context.from_dict(dict(
            user='user',
            tenant='tenant',
        ))

        mock_init.assert_called_once_with(user='user', tenant='tenant')
        self.assertIsInstance(result, context.Context)

    def test_to_dict(self):
        ctx = context.Context('user', 'tenant', roles=['one', 'two'],
                              request_id='request_id', is_admin=True)

        result = ctx.to_dict()

        self.assertEqual(result, dict(
            user='user',
            tenant='tenant',
            roles=['one', 'two'],
            request_id='request_id',
            is_admin=True,
        ))

    def test_elevated_nonadmin(self):
        ctx = context.Context('user', 'tenant', roles=['one', 'two'],
                              request_id='request_id', is_admin=False)
        ctx.session = mock.Mock()

        elev_ctx = ctx.elevated()

        self.assertNotEqual(id(ctx), id(elev_ctx))
        self.assertEqual(elev_ctx.user, 'user')
        self.assertEqual(elev_ctx.tenant, 'tenant')
        self.assertEqual(elev_ctx.roles, ['one', 'two', 'admin'])
        self.assertEqual(elev_ctx.request_id, 'request_id')
        self.assertEqual(elev_ctx.is_admin, True)
        self.assertEqual(id(elev_ctx.session), id(ctx.session))

    def test_elevated_admin(self):
        ctx = context.Context('user', 'tenant', roles=['one', 'aDmIn', 'two'],
                              request_id='request_id', is_admin=True)
        ctx.session = 'session'

        elev_ctx = ctx.elevated()

        self.assertNotEqual(id(ctx), id(elev_ctx))
        self.assertEqual(elev_ctx.user, 'user')
        self.assertEqual(elev_ctx.tenant, 'tenant')
        self.assertEqual(elev_ctx.roles, ['one', 'aDmIn', 'two'])
        self.assertEqual(elev_ctx.request_id, 'request_id')
        self.assertEqual(elev_ctx.is_admin, True)
        self.assertEqual(id(elev_ctx.session), id(ctx.session))


class GetAdminContextTestCase(tests.TestCase):
    @mock.patch.object(context, 'Context', return_value='context')
    def test_get_admin_context(self, mock_Context):
        result = context.get_admin_context()

        mock_Context.assert_called_once_with(user=None, tenant=None,
                                             roles=['admin'], is_admin=True)
        self.assertEqual(result, 'context')
