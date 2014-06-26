"""Initial Version

Revision ID: 3a2964d51f2
Revises: None
Create Date: 2014-06-25 17:29:27.974771

"""

# revision identifiers, used by Alembic.
revision = '3a2964d51f2'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
	op.create_table(
		'People',
		sa.Column('id', sa.Integer, primary_key=True),
		sa.Column('first_name', sa.String(50)),
		sa.Column('last_name', sa.String(50)),
		sa.Column('age', sa.String(3)),
		sa.Column('department', sa.String(50)),
		sa.Column('college', sa.String(50)),
		)

	op.create_table(
		'Accounts',
		sa.Column('id', sa.Integer, primary_key=True),
		sa.Column('username', sa.String(50)),
		sa.Column('password', sa.String(50)),
		)



def downgrade():
	op.drop_table('People')
	op.drop_table('Account')
