import pytest
from pynamodb.attributes import UnicodeAttribute, NumberAttribute
from pynamodb.models import Model

from ..utils import get_key_name


def test_getkeyname_should_raiseerror():
    with pytest.raises(TypeError):
        get_key_name(object)


def test_getkeyname_should_workonstrings():
    class MyModel(Model):
        class Meta:
            table_name = 'some-table'

        notmyid = UnicodeAttribute(null=True)
        myid = UnicodeAttribute(hash_key=True)

    assert get_key_name(MyModel) == 'myid'


def test_getkeyname_should_workonnumbers():
    class MyModel(Model):
        class Meta:
            table_name = 'some-table'

        notmyid = UnicodeAttribute(null=True)
        myid = NumberAttribute(hash_key=True)

    assert get_key_name(MyModel) == 'myid'
