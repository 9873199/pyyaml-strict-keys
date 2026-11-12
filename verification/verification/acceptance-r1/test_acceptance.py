import pytest
import yaml
from yaml.constructor import ConstructorError

def strict(text):return yaml.strict_safe_load(text)
@pytest.mark.parametrize('text',['role: reader\nrole: writer','true: a\n1: b','1: a\n01: b','1: a\n0x1: b','nested:\n  x: a\n  x: b','? &k same\n: a\n? *k\n: b','? &k .nan\n: a\n? *k\n: b'])
def test_constructed_explicit_collisions_rejected(text):
 with pytest.raises(ConstructorError):strict(text)
def test_error_locates_both_key_occurrences():
 with pytest.raises(ConstructorError) as got:strict('heading: value\nrole: reader\nrole: writer')
 assert got.value.context_mark.line==1 and got.value.problem_mark.line==2
def test_merge_default_can_be_explicitly_overridden():
 assert strict('base: &b {role: reader}\nactual: {<<: *b, role: writer}')['actual']=={'role':'writer'}
def test_two_sources_keep_original_precedence():
 text='left: &l {x: 1, y: 2}\nright: &r {x: 3, z: 4}\nactual: {<<: [*l, *r], y: 5}'
 assert strict(text)==yaml.safe_load(text)
def test_same_merge_source_shared_by_aliases():
 text='source: &s {x: 1}\nfirst: {<<: *s, y: 2}\nsecond: {<<: *s, x: 3}'
 assert strict(text)==yaml.safe_load(text)
def test_bad_source_cannot_be_laundered_by_merge():
 with pytest.raises(ConstructorError):strict('source: &s {x: 1, x: 2}\nactual: {<<: *s}')
def test_repeated_explicit_key_after_merge_still_fails():
 with pytest.raises(ConstructorError):strict('base: &b {x: 0}\nactual: {<<: *b, x: 1, x: 2}')
def test_two_merge_keys_refused():
 with pytest.raises(ConstructorError):strict('left: &l {x: 1}\nright: &r {y: 2}\nactual: {<<: *l, <<: *r}')
def test_recursive_alias_is_preserved():
 value=strict('a: &a {self: *a}');assert value['a']['self'] is value['a']
def test_unhashable_key_is_constructor_error():
 with pytest.raises(ConstructorError):strict('? [a,b]\n: value')
def test_multi_document_and_failure_do_not_contaminate_next_load():
 assert list(yaml.strict_safe_load_all('x: 1\n---\nx: 2'))==[{'x':1},{'x':2}]
 with pytest.raises(ConstructorError):list(yaml.strict_safe_load_all('x: 1\n---\nx: 2\nx: 3'))
 assert strict('x: 4')=={'x':4}
def test_legacy_loader_and_constructor_registry_unchanged():
 constructors=dict(yaml.SafeLoader.yaml_constructors)
 assert strict('x: 1')=={'x':1};assert yaml.safe_load('x: 1\nx: 2')=={'x':2};assert yaml.SafeLoader.yaml_constructors==constructors
 assert yaml.load('x: 3',Loader=yaml.StrictSafeLoader)=={'x':3}
def test_nested_merged_source_reused_keeps_explicit_origin():
 text='base: &b {x: 0, y: 1}\nmid: &m {<<: *b, x: 2}\nfirst: {<<: *m}\nsecond: {<<: *m, x: 3}'
 # Initial f5e4504 has existing key-identity deduplication across a flattened
 # source. Do not impose a repair of that unrelated legacy value choice.
 value=strict(text)
 assert value['mid']['x']==2 and value['second']['x']==3
 assert all(value[name]['y']==1 for name in ('base','mid','first','second'))

def test_duplicate_inside_inline_merge_source_rejected():
 with pytest.raises(ConstructorError):strict('actual: {<<: {x: 1, x: 2}}')

def test_equal_hash_but_unequal_business_keys_remain_distinct():
 assert strict('1: number\n"1": text\n"true": word\n0: zero')=={1:'number','1':'text','true':'word',0:'zero'}

def test_float_integer_key_collision_rejected():
 with pytest.raises(ConstructorError):strict('1: integer\n1.0: float')

def test_loader_dispose_then_fresh_document_after_collision():
 loader=yaml.StrictSafeLoader('role: a\nrole: b')
 try:
  with pytest.raises(ConstructorError):loader.get_single_data()
 finally:loader.dispose()
 assert yaml.strict_safe_load('role: next')=={'role':'next'}