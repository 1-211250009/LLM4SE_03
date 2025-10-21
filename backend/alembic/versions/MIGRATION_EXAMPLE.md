# 数据库迁移示例

当你配置好数据库后，运行以下命令会在这个目录生成迁移文件：

```bash
alembic revision --autogenerate -m "Initial migration - create users table"
```

这会生成一个类似这样的文件：`xxxx_initial_migration_create_users_table.py`

## 示例迁移文件内容

```python
"""Initial migration - create users table

Revision ID: abc123def456
Revises: 
Create Date: 2025-10-20 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = 'abc123def456'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema"""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade() -> None:
    """Downgrade database schema"""
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
```

## 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 回滚一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision_id>

# 回滚所有
alembic downgrade base
```

## 常用命令

```bash
# 生成迁移（自动检测模型变化）
alembic revision --autogenerate -m "描述你的修改"

# 手动创建空迁移
alembic revision -m "手动迁移说明"

# 显示SQL而不执行
alembic upgrade head --sql

# 标记为已执行（不实际执行SQL）
alembic stamp head
```

