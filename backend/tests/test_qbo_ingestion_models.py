from app.models.client_group import ClientGroupEntity
from app.models.qbo_ingestion import (
    ClientGroupTaxYear,
    ImportRun,
    TrialBalanceLine,
    TrialBalanceSnapshot,
)


def test_client_group_tax_year_constraint():
    constraints = {constraint.name for constraint in ClientGroupTaxYear.__table__.constraints}
    assert "uq_client_group_tax_year" in constraints


def test_import_run_columns():
    columns = ImportRun.__table__.columns
    assert "status" in columns
    assert "period_end_date" in columns
    assert "tax_year" in columns


def test_trial_balance_snapshot_fields():
    columns = TrialBalanceSnapshot.__table__.columns
    assert "source" in columns
    assert "run_type" in columns
    assert "period_end_date" in columns


def test_trial_balance_line_has_tenant():
    assert "tenant_id" in TrialBalanceLine.__table__.columns


def test_client_group_entity_metadata_columns():
    columns = ClientGroupEntity.__table__.columns
    for column_name in ("start_date", "end_date", "tags", "notes"):
        assert column_name in columns
