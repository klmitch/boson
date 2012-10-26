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

"""
Initial revision

Revision ID: 1f22e3c5ff66
Revises: None
Create Date: 2012-10-26 17:37:18.592202
"""

# revision identifiers, used by Alembic.
revision = '1f22e3c5ff66'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    """
    Create the tables.
    """

    op.create_table(
        'services',
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('auth_fields', sa.Text),
    )

    op.create_table(
        'categories',
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('service_id', sa.String(36), sa.ForeignKey('services.id'),
                  nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('usage_fset', sa.Text),
        sa.Column('quota_fsets', sa.Text),
    )

    op.create_table(
        'resources',
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('service_id', sa.String(36), sa.ForeignKey('services.id'),
                  nullable=False),
        sa.Column('category_id', sa.String(36), sa.ForeignKey('categories.id'),
                  nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('parameters', sa.Text),
        sa.Column('absolute', sa.Boolean, nullable=False),
    )

    op.create_table(
        'usages',
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('resource_id', sa.String(36), sa.ForeignKey('resources.id'),
                  nullable=False),
        sa.Column('parameter_data', sa.Text),
        sa.Column('auth_data', sa.Text),
        sa.Column('used', sa.BigInteger, nullable=False),
        sa.Column('reserved', sa.BigInteger, nullable=False),
        sa.Column('until_refresh', sa.Integer),
        sa.Column('refresh_id', sa.String(36)),
    )

    op.create_table(
        'quotas',
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('resource_id', sa.String(36), sa.ForeignKey('resources.id'),
                  nullable=False),
        sa.Column('auth_data', sa.Text),
        sa.Column('limit', sa.BigInteger),
    )

    op.create_table(
        'reservations',
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('expire', sa.DateTime, nullable=False),
    )

    op.create_table(
        'reserved_items',
        sa.Column('created_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('reservation_id', sa.String(36),
                  sa.ForeignKey('reservations.id'), nullable=False),
        sa.Column('resource_id', sa.String(36), sa.ForeignKey('resources.id'),
                  nullable=False),
        sa.Column('usage_id', sa.String(36), sa.ForeignKey('usages.id'),
                  nullable=False),
        sa.Column('delta', sa.BigInteger, nullable=False),
    )


def downgrade():
    """
    Drop the tables.
    """

    op.drop_table('services')
    op.drop_table('categories')
    op.drop_table('resources')
    op.drop_table('usages')
    op.drop_table('quotas')
    op.drop_table('reservations')
    op.drop_table('reserved_items')
