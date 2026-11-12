"""Independent checks of duplicate error locations and literal business keys."""
import pytest,yaml
from yaml.constructor import ConstructorError

@pytest.mark.parametrize('key',['same','.nan'])
def test_alias_key_duplicate_reports_distinct_source_occurrences(key):
 text='? &key '+key+'\n: first\n? *key\n: second\n'
 with pytest.raises(ConstructorError) as caught:yaml.strict_safe_load(text)
 error=caught.value
 assert error.context_mark.line==0
 assert error.problem_mark.line==2

def test_nested_duplicate_reports_both_key_lines():
 text='header: present\nnested:\n  role: reader\n  role: writer\n'
 with pytest.raises(ConstructorError) as caught:yaml.strict_safe_load(text)
 assert caught.value.context_mark.line==2
 assert caught.value.problem_mark.line==3

def test_quoted_merge_spelling_is_an_ordinary_business_key():
 text='base: &b {x: 1}\nactual: {<<: *b, "<<": literal}'
 assert yaml.strict_safe_load(text)==yaml.safe_load(text)
 assert yaml.strict_safe_load(text)['actual']=={'x':1,'<<':'literal'}

def test_false_zero_explicit_collision_is_rejected():
 with pytest.raises(ConstructorError):yaml.strict_safe_load('false: flag\n0: number')
