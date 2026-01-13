from app.models.entity import QBOConnection


def test_qbo_connection_unique_constraints():
    constraint_names = {constraint.name for constraint in QBOConnection.__table__.constraints}
    assert "uq_qbo_connections_entity" in constraint_names
    assert "uq_qbo_connections_tenant_realm" in constraint_names
