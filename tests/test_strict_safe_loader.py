import pytest

import yaml
from yaml.constructor import (
    ConstructorError, SafeConstructor, StrictSafeConstructor,
)
from yaml.loader import StrictSafeLoader


def assert_duplicate_key_error(exc, first_line, second_line):
    """The error must locate both the first and the second occurrence."""
    assert isinstance(exc, ConstructorError)
    assert exc.context_mark is not None
    assert exc.problem_mark is not None
    # The mapping context points at the mapping containing the collision.
    assert exc.context_mark.line + 1 == first_line or \
        exc.problem_mark.line + 1 == second_line
    # The problem mark is the second occurrence; the first occurrence is
    # rendered as part of the problem message.
    assert exc.problem_mark.line + 1 == second_line
    assert str(first_line) in str(exc)


# ---------------------------------------------------------------------------
# Basic duplicate detection, comparing constructed keys rather than source
# ---------------------------------------------------------------------------

def test_plain_duplicate_string_key():
    source = """
role: reader
role: writer
"""
    with pytest.raises(ConstructorError) as exc_info:
        yaml.strict_safe_load(source)
    assert_duplicate_key_error(exc_info.value, first_line=2, second_line=3)


def test_duplicate_integer_key():
    source = """
1: a
1: b
"""
    with pytest.raises(ConstructorError) as exc_info:
        yaml.strict_safe_load(source)
    assert_duplicate_key_error(exc_info.value, first_line=2, second_line=3)


def test_different_integer_spellings_collide():
    # 0x10 and 16 construct to the same Python int although their source
    # strings differ completely.
    source = """
0x10: a
16: b
"""
    with pytest.raises(ConstructorError):
        yaml.strict_safe_load(source)


def test_bool_and_int_collide():
    # In Python True == 1 and hash(True) == hash(1), so these collide in a
    # dict even though the source text is unrelated.
    source = """
true: a
1: b
"""
    with pytest.raises(ConstructorError) as exc_info:
        yaml.strict_safe_load(source)
    assert_duplicate_key_error(exc_info.value, first_line=2, second_line=3)


def test_float_and_int_collide():
    source = """
1: a
1.0: b
"""
    with pytest.raises(ConstructorError):
        yaml.strict_safe_load(source)


def test_different_bool_spellings_collide():
    # YAML 1.1 resolves both 'yes' and 'true' to Python's True.
    source = """
yes: a
true: b
"""
    with pytest.raises(ConstructorError):
        yaml.strict_safe_load(source)


def test_duplicate_key_in_nested_mapping_reports_inner_marks():
    source = """
outer:
  inner:
    k: 1
    k: 2
"""
    with pytest.raises(ConstructorError) as exc_info:
        yaml.strict_safe_load(source)
    assert_duplicate_key_error(exc_info.value, first_line=4, second_line=5)


def test_alias_of_same_key_is_detected():
    # Explicit keys need the value on a separate line; otherwise the whole
    # '? *k : first' line parses as a nested mapping used as key.
    source = """
keyholder: &k 5
mapping:
  ? *k
  : first
  ? *k
  : second
"""
    with pytest.raises(ConstructorError) as exc_info:
        yaml.strict_safe_load(source)
    exc = exc_info.value
    # The collision is detected by constructed value even though both key
    # nodes are the same aliased node.  The composed representation tree
    # reuses the anchor node for aliases, so both marks locate the anchor
    # definition; the first-occurrence location is in the message and the
    # second occurrence is the problem mark.
    assert "found duplicate key" in str(exc)
    assert "line 2" in str(exc)
    assert exc.context_mark.line + 1 == 4
    assert exc.problem_mark.line + 1 == 2
    assert exc.problem_mark.column + 1 == 12


def test_aliased_key_and_inline_key_collide():
    source = """
keyholder: &k 5
mapping:
  ? *k
  : first
  5: second
"""
    with pytest.raises(ConstructorError):
        yaml.strict_safe_load(source)


def test_distinct_equal_scalar_nodes_are_still_compared():
    # Two separate scalar nodes (not aliases) that construct to the same
    # integer must be compared by constructed value.  Leading-zero octal is
    # the int spelling supported by this YAML 1.1 resolver.
    source = """
mapping:
  010: octal
  8: decimal
"""
    with pytest.raises(ConstructorError):
        yaml.strict_safe_load(source)


def test_unique_keys_load_normally():
    source = """
name: config
roles:
  reader: 1
  writer: 2
ports:
  80: http
  443: https
"""
    assert yaml.strict_safe_load(source) == {
        "name": "config",
        "roles": {"reader": 1, "writer": 2},
        "ports": {80: "http", 443: "https"},
    }


def test_strict_matches_safe_on_valid_input():
    source = """
- one
- two: 2
  three: 3
- 2020-01-01
- true
- null
"""
    assert yaml.strict_safe_load(source) == yaml.safe_load(source)


# ---------------------------------------------------------------------------
# Merge keys: keep the documented semantics, reject the genuinely invalid ones
# ---------------------------------------------------------------------------

def test_merge_then_explicit_override_is_allowed():
    source = """
base: &base
  x: 1
  y: 2
target:
  <<: *base
  x: 9
"""
    result = yaml.strict_safe_load(source)
    assert result["target"] == {"x": 9, "y": 2}


def test_overlapping_merge_sources_keep_priority():
    source = """
first: &first
  x: 1
  y: 2
second: &second
  x: 9
  z: 3
target:
  <<: [*first, *second]
  w: 4
"""
    result = yaml.strict_safe_load(source)
    # The earlier merge source wins, exactly as SafeLoader resolves it.
    assert result["target"] == {"x": 1, "y": 2, "z": 3, "w": 4}


def test_same_merge_source_used_twice_is_allowed():
    source = """
base: &base {x: 1, y: 2}
target:
  <<: [*base, *base]
  z: 3
"""
    result = yaml.strict_safe_load(source)
    assert result["target"] == {"x": 1, "y": 2, "z": 3}


def test_two_explicit_merge_keys_are_rejected():
    source = """
base: &base {x: 1}
other: &other {y: 2}
target:
  <<: *base
  <<: *other
  z: 3
"""
    with pytest.raises(ConstructorError) as exc_info:
        yaml.strict_safe_load(source)
    assert "merge key" in str(exc_info.value)
    # The second '<<' is on line 6.
    assert exc_info.value.problem_mark.line + 1 == 6


def test_duplicate_key_inside_aliased_merge_source_is_rejected():
    source = """
base: &base
  x: 1
  x: 2
target:
  <<: *base
"""
    with pytest.raises(ConstructorError) as exc_info:
        yaml.strict_safe_load(source)
    assert_duplicate_key_error(exc_info.value, first_line=3, second_line=4)


def test_duplicate_key_inside_inline_merge_source_is_rejected():
    # The inline merge mapping is never constructed as a standalone value;
    # flatten_mapping copies its pairs and drops the '<<' pair, so the check
    # must run while flattening rather than only in construct_mapping.
    source = """
target:
  <<: {x: 1, x: 2}
  y: 3
"""
    with pytest.raises(ConstructorError) as exc_info:
        yaml.strict_safe_load(source)
    assert_duplicate_key_error(exc_info.value, first_line=3, second_line=3)


def test_duplicate_key_inside_nested_merge_source_is_rejected():
    source = """
inner: &inner
  k: 1
  k: 2
outer: &outer
  <<: *inner
  q: 3
target:
  <<: *outer
"""
    with pytest.raises(ConstructorError):
        yaml.strict_safe_load(source)


def test_alias_revisited_after_flatten_keeps_explicit_information():
    # 'base' is merged into two targets; its own explicit pairs must not be
    # mistaken for explicit pairs of the targets after flatten_mapping has
    # mutated the nodes.
    source = """
base: &base {x: 1, y: 2}
t1: {<<: *base}
t2:
  <<: *base
  z: 3
"""
    result = yaml.strict_safe_load(source)
    assert result["t1"] == {"x": 1, "y": 2}
    assert result["t2"] == {"x": 1, "y": 2, "z": 3}


# ---------------------------------------------------------------------------
# Unhashable keys and other structural cases
# ---------------------------------------------------------------------------

def test_unhashable_key_raises_constructor_error():
    source = """
[1, 2]: value
"""
    with pytest.raises(ConstructorError) as exc_info:
        yaml.strict_safe_load(source)
    assert "unhashable key" in str(exc_info.value)


def test_unhashable_key_inside_nested_mapping():
    source = """
outer:
  [a, b]: value
"""
    with pytest.raises(ConstructorError) as exc_info:
        yaml.strict_safe_load(source)
    assert "unhashable key" in str(exc_info.value)


def test_recursive_alias_loads():
    source = """
a: &a
  b: *a
"""
    result = yaml.strict_safe_load(source)
    assert result["a"]["b"] is result["a"]


def test_recursive_alias_through_merge_loads():
    source = """
a: &a
  <<: *a
  x: 1
"""
    result = yaml.strict_safe_load(source)
    assert result["a"]["x"] == 1


def test_set_with_duplicate_entries_is_rejected():
    source = """
!!set
? 1
? 1
"""
    with pytest.raises(ConstructorError):
        yaml.strict_safe_load(source)


# ---------------------------------------------------------------------------
# Multi-document loading and state isolation
# ---------------------------------------------------------------------------

def test_strict_safe_load_all_happy_path():
    source = """
a: 1
---
b: 2
---
- c
- d
"""
    assert list(yaml.strict_safe_load_all(source)) == [
        {"a": 1}, {"b": 2}, ["c", "d"],
    ]


def test_state_does_not_leak_into_next_document_after_error():
    source = """
dup: 1
dup: 2
---
good: 3
fine: 4
"""
    loader = StrictSafeLoader(source)
    try:
        with pytest.raises(ConstructorError):
            loader.get_data()
        # The failed document must not leave any check state behind.
        assert loader.strict_checked_nodes == set()
        assert loader.strict_key_checked_nodes == set()
        assert loader.strict_explicit_pairs == {}
        assert loader.get_data() == {"good": 3, "fine": 4}
    finally:
        loader.dispose()


def test_error_in_one_document_does_not_affect_fresh_loader():
    bad = "k: 1\nk: 2\n"
    good = "k: 1\nj: 2\n"
    with pytest.raises(ConstructorError):
        yaml.strict_safe_load(bad)
    # A brand new loader on different input works normally.
    assert yaml.strict_safe_load(good) == {"k": 1, "j": 2}


# ---------------------------------------------------------------------------
# The classic SafeLoader path and its constructor tables stay untouched
# ---------------------------------------------------------------------------

def test_safe_load_keeps_last_value_wins_behavior():
    source = """
role: reader
role: writer
"""
    # Old behavior must be unchanged.
    assert yaml.safe_load(source) == {"role": "writer"}


def test_global_safe_loader_constructor_table_is_not_modified():
    # StrictSafeConstructor never registers its own constructors, so the
    # shared class table is the very same object SafeLoader/SafeConstructor
    # use.
    assert StrictSafeLoader.yaml_constructors is \
        yaml.SafeLoader.yaml_constructors
    assert StrictSafeConstructor.yaml_constructors is \
        SafeConstructor.yaml_constructors


def test_strict_loader_is_pure_python():
    from yaml.reader import Reader
    assert issubclass(StrictSafeLoader, Reader)
    assert not hasattr(yaml, "CStrictSafeLoader")


def test_direct_flatten_mapping_rejects_double_merge():
    source = """
base: &base {x: 1}
target:
  <<: *base
  <<: *base
"""
    loader = StrictSafeLoader(source)
    try:
        root = loader.get_single_node()
        target = next(
            value_node for key_node, value_node in root.value
            if key_node.value == "target"
        )
        with pytest.raises(ConstructorError):
            loader.flatten_mapping(target)
    finally:
        loader.dispose()
