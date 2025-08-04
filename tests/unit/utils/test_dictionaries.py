from apolo_app_types.helm.utils.dictionaries import get_nested_values


def test_get_nested_keys():
    sample_dict = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
    keys_to_retrieve = ["a", "b.c", "e"]
    expected_output = {"a": 1, "b": {"c": 2}, "e": 4}
    assert get_nested_values(sample_dict, keys_to_retrieve) == expected_output
