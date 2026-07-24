from apolo_app_types.protocols.common.containers import ContainerImage


def test_subclass_does_not_mutate_parent_x_type() -> None:
    class ChildImage(ContainerImage):
        pass

    assert ContainerImage.model_json_schema()["x-type"] == "ContainerImage"
    assert ChildImage.model_json_schema()["x-type"] == "ChildImage"


def test_nested_subclass_chain_keeps_distinct_x_types() -> None:
    class Base(ContainerImage):
        pass

    class Leaf(Base):
        pass

    assert ContainerImage.model_json_schema()["x-type"] == "ContainerImage"
    assert Base.model_json_schema()["x-type"] == "Base"
    assert Leaf.model_json_schema()["x-type"] == "Leaf"
