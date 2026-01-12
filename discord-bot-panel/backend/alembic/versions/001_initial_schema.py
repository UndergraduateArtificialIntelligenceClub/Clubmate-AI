"""Initial Schema - All Tables

Revision ID: 001
Revises: 
Create Date: 2026-01-11

Creates all initial tables:
- users: Admin accounts with Discord auth
- contacts: General contact storage
- files: File metadata
- api_keys: Encrypted API key storage  
- activity_logs: Audit trail
- oauth_tokens: OAuth credential storage
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables."""
    
    # ============================================================
    # USERS TABLE
    # Admin accounts authenticated via Discord
    # ============================================================
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('discord_id', sa.String(32), unique=True, nullable=False),
        sa.Column('username', sa.String(32), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.String(512), nullable=True),
        sa.Column('role', sa.Integer(), default=1, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_users_discord_id', 'users', ['discord_id'])
    op.create_index('idx_users_role', 'users', ['role'])
    
    # ============================================================
    # CONTACTS TABLE
    # General contact storage
    # ============================================================
    op.create_table(
        'contacts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(32), nullable=True),
        sa.Column('discord_id', sa.String(32), nullable=True),
        sa.Column('discord_username', sa.String(32), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_contacts_email', 'contacts', ['email'])
    op.create_index('idx_contacts_discord_id', 'contacts', ['discord_id'])
    
    # ============================================================
    # FILES TABLE
    # Uploaded file metadata
    # ============================================================
    op.create_table(
        'files',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('storage_path', sa.String(512), unique=True, nullable=False),
        sa.Column('mime_type', sa.String(128), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_files_uploaded_by', 'files', ['uploaded_by'])
    
    # ============================================================
    # API_KEYS TABLE  
    # Encrypted API key storage
    # ============================================================
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('encrypted_value', sa.Text(), nullable=False),
        sa.Column('key_hash', sa.String(64), unique=True, nullable=False),
        sa.Column('masked', sa.String(32), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_api_keys_user_active', 'api_keys', ['user_id', 'is_active'])
    op.create_index('idx_api_keys_hash', 'api_keys', ['key_hash'])
    
    # ============================================================
    # ACTIVITY_LOGS TABLE
    # Audit trail
    # ============================================================
    op.create_table(
        'activity_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_logs_user_id', 'activity_logs', ['user_id'])
    op.create_index('idx_logs_action', 'activity_logs', ['action'])
    op.create_index('idx_logs_created_at', 'activity_logs', ['created_at'])
    
    # ============================================================
    # OAUTH_TOKENS TABLE
    # OAuth credential storage
    # ============================================================
    op.create_table(
        'oauth_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(32), default='google', nullable=False),
        sa.Column('access_token_encrypted', sa.Text(), nullable=False),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('token_type', sa.String(32), default='Bearer', nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scope', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_oauth_user_provider', 'oauth_tokens', ['user_id', 'provider'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('oauth_tokens')
    op.drop_table('activity_logs')
    op.drop_table('api_keys')
    op.drop_table('files')
    op.drop_table('contacts')
    op.drop_table('users')
