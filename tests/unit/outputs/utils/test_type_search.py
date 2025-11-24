"""Tests for type search utilities."""

from pydantic import BaseModel

from apolo_app_types.outputs.utils.type_search import (
    find_instances_recursive,
    find_instances_recursive_simple,
)


# Test models
class TargetType(BaseModel):
    """Target type to search for."""

    value: str


class NestedModel(BaseModel):
    """Model with nested target."""

    name: str
    target: TargetType | None = None


class ComplexModel(BaseModel):
    """Complex model with various nesting patterns."""

    simple_target: TargetType | None = None
    nested: NestedModel | None = None
    target_list: list[TargetType] | None = None
    nested_list: list[NestedModel] | None = None
    target_dict: dict[str, TargetType] | None = None


class CircularModel(BaseModel):
    """Model that could cause circular references."""

    name: str
    children: list["CircularModel"] = []
    target: TargetType | None = None


class TestFindInstancesRecursive:
    """Tests for the find_instances_recursive function."""

    def test_finds_direct_instance(self):
        """Test finding a direct instance at root level."""
        target = TargetType(value="root")

        results = find_instances_recursive(target, TargetType)

        assert len(results) == 1
        assert results[0][0] == "root"
        assert results[0][1].value == "root"

    def test_finds_nested_instance(self):
        """Test finding an instance nested in a model."""
        model = NestedModel(
            name="test",
            target=TargetType(value="nested"),
        )

        results = find_instances_recursive(model, TargetType)

        assert len(results) == 1
        assert results[0][0] == "target"
        assert results[0][1].value == "nested"

    def test_finds_deeply_nested_instance(self):
        """Test finding an instance deeply nested."""
        model = ComplexModel(
            nested=NestedModel(
                name="test",
                target=TargetType(value="deep"),
            )
        )

        results = find_instances_recursive(model, TargetType)

        assert len(results) == 1
        assert results[0][0] == "nested.target"
        assert results[0][1].value == "deep"

    def test_finds_multiple_instances(self):
        """Test finding multiple instances at different locations."""
        model = ComplexModel(
            simple_target=TargetType(value="simple"),
            nested=NestedModel(
                name="test",
                target=TargetType(value="nested"),
            ),
        )

        results = find_instances_recursive(model, TargetType)

        assert len(results) == 2
        values = {r[1].value for r in results}
        assert values == {"simple", "nested"}

    def test_finds_instances_in_list(self):
        """Test finding instances in a list."""
        model = ComplexModel(
            target_list=[
                TargetType(value="first"),
                TargetType(value="second"),
                TargetType(value="third"),
            ]
        )

        results = find_instances_recursive(model, TargetType)

        assert len(results) == 3
        paths = {r[0] for r in results}
        assert paths == {"target_list[0]", "target_list[1]", "target_list[2]"}

    def test_finds_instances_in_nested_list(self):
        """Test finding instances in a list of nested models."""
        model = ComplexModel(
            nested_list=[
                NestedModel(name="a", target=TargetType(value="first")),
                NestedModel(name="b", target=TargetType(value="second")),
            ]
        )

        results = find_instances_recursive(model, TargetType)

        assert len(results) == 2
        paths = {r[0] for r in results}
        assert paths == {"nested_list[0].target", "nested_list[1].target"}

    def test_finds_instances_in_dict(self):
        """Test finding instances in a dictionary."""
        model = ComplexModel(
            target_dict={
                "key1": TargetType(value="first"),
                "key2": TargetType(value="second"),
            }
        )

        results = find_instances_recursive(model, TargetType)

        assert len(results) == 2
        paths = {r[0] for r in results}
        assert paths == {"target_dict['key1']", "target_dict['key2']"}

    def test_handles_none_values(self):
        """Test that None values are handled gracefully."""
        model = ComplexModel(
            simple_target=None,
            nested=None,
            target_list=None,
        )

        results = find_instances_recursive(model, TargetType)

        assert len(results) == 0

    def test_handles_empty_collections(self):
        """Test that empty collections are handled gracefully."""
        model = ComplexModel(
            target_list=[],
            nested_list=[],
            target_dict={},
        )

        results = find_instances_recursive(model, TargetType)

        assert len(results) == 0

    def test_handles_circular_references(self):
        """Test that circular references don't cause infinite loops."""
        parent = CircularModel(name="parent")
        child = CircularModel(
            name="child",
            target=TargetType(value="found"),
        )
        parent.children = [child]
        # Create circular reference
        child.children = [parent]

        results = find_instances_recursive(parent, TargetType)

        # Should find the target without infinite loop
        assert len(results) == 1
        assert results[0][1].value == "found"

    def test_finds_instances_in_plain_list(self):
        """Test finding instances in a plain list (not in a model)."""
        items = [
            TargetType(value="first"),
            TargetType(value="second"),
        ]

        results = find_instances_recursive(items, TargetType)

        assert len(results) == 2
        paths = {r[0] for r in results}
        assert paths == {"[0]", "[1]"}

    def test_finds_instances_in_plain_dict(self):
        """Test finding instances in a plain dictionary."""
        items = {
            "a": TargetType(value="first"),
            "b": TargetType(value="second"),
        }

        results = find_instances_recursive(items, TargetType)

        assert len(results) == 2
        paths = {r[0] for r in results}
        assert paths == {"['a']", "['b']"}

    def test_finds_instances_in_tuple(self):
        """Test finding instances in a tuple."""
        items = (
            TargetType(value="first"),
            TargetType(value="second"),
        )

        results = find_instances_recursive(items, TargetType)

        assert len(results) == 2

    def test_finds_instances_in_set(self):
        """Test finding instances in a set."""
        # Use hashable types for set test
        items = {"first", "second", "third"}

        # Search for strings in the set
        results = find_instances_recursive(items, str)

        assert len(results) == 3

    def test_returns_empty_for_no_matches(self):
        """Test that empty list is returned when no matches found."""
        model = NestedModel(name="test", target=None)

        results = find_instances_recursive(model, TargetType)

        assert results == []

    def test_handles_primitive_types(self):
        """Test that primitive types don't cause errors."""
        results = find_instances_recursive("string", TargetType)
        assert results == []

        results = find_instances_recursive(123, TargetType)
        assert results == []

        results = find_instances_recursive(None, TargetType)
        assert results == []


class TestFindInstancesRecursiveSimple:
    """Tests for the find_instances_recursive_simple function."""

    def test_returns_instances_without_paths(self):
        """Test that only instances are returned without path information."""
        model = ComplexModel(
            simple_target=TargetType(value="simple"),
            nested=NestedModel(
                name="test",
                target=TargetType(value="nested"),
            ),
        )

        results = find_instances_recursive_simple(model, TargetType)

        assert len(results) == 2
        values = {r.value for r in results}
        assert values == {"simple", "nested"}

    def test_returns_empty_list_for_no_matches(self):
        """Test that empty list is returned when no matches found."""
        model = NestedModel(name="test", target=None)

        results = find_instances_recursive_simple(model, TargetType)

        assert results == []

    def test_finds_all_instances_in_complex_structure(self):
        """Test finding all instances in a complex nested structure."""
        model = ComplexModel(
            simple_target=TargetType(value="1"),
            nested=NestedModel(name="test", target=TargetType(value="2")),
            target_list=[TargetType(value="3"), TargetType(value="4")],
            target_dict={"a": TargetType(value="5")},
        )

        results = find_instances_recursive_simple(model, TargetType)

        assert len(results) == 5
        values = {r.value for r in results}
        assert values == {"1", "2", "3", "4", "5"}
