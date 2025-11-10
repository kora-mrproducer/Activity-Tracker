# Database Migrations with Flask-Migrate

This project uses Flask-Migrate (Alembic) for database schema management.

## Initial Setup

The migrations folder has been initialized and an initial migration has been created.

## Common Commands

### Apply Migrations (Upgrade Database)
```bash
flask db upgrade
```

### Create a New Migration (after changing models)
```bash
flask db migrate -m "Description of changes"
```

### View Migration History
```bash
flask db history
```

### Rollback Last Migration
```bash
flask db downgrade
```

### Rollback to Specific Migration
```bash
flask db downgrade <revision_id>
```

## Migration Workflow

1. **Make changes** to models in `app/models.py`
2. **Generate migration**: `flask db migrate -m "Add new column"`
3. **Review** the generated migration file in `migrations/versions/`
4. **Apply migration**: `flask db upgrade`

## Notes

- Flask-Migrate automatically detects model changes
- Always review generated migrations before applying
- Backup your database before running migrations in production
- The manual `ensure_update_bp_column()` function has been removed
