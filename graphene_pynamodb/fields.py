from __future__ import absolute_import

from functools import partial

from graphene import relay
from graphene.relay.connection import PageInfo
from graphql_relay.connection.connectiontypes import Edge

from graphene_pynamodb.utils import get_key_name


class PynamoConnectionField(relay.ConnectionField):
    def __init__(self, type, *args, **kwargs):
        super(PynamoConnectionField, self).__init__(
            type,
            *args,
            **kwargs
        )

    @property
    def model(self):
        return self.type._meta.node._meta.model

    @classmethod
    def get_query(cls, model, context, info, args):
        return model.scan

    @classmethod
    def connection_resolver(cls, resolver, connection, model, root, args, context, info):
        iterable = resolver(root, args, context, info)

        first = args.get('first')
        after = args.get('after')
        last = args.get('last')
        before = args.get('before')
        has_previous_page = bool(after)
        page_size = first if first else last if last else None
        connection_type = connection
        pageinfo_type = PageInfo

        # get the results from the attribute requested (relationship)
        if not iterable and root and hasattr(root, info.field_name):
            iterable = getattr(root, info.field_name)

        # get a full scan query since we have no root
        if not iterable and not root:
            query = cls.get_query(model, context, info, args)
            iterable = query()
            if first or last or after or before:
                raise NotImplementedError(
                    "DynamoDB scan operations have no predictable sort. Arguments first, last, after " +
                    "and before will have unpredictable results")

        iterable = iterable if isinstance(iterable, list) else list(iterable)

        if last:
            iterable = iterable[-last:]

        (has_next, edges) = cls.get_edges_from_iterable(iterable, model, edge_type=connection.Edge, after=after,
                                                        page_size=page_size)

        key_name = get_key_name(model)
        try:
            start_cursor = getattr(edges[0].node, key_name)
            end_cursor = getattr(edges[-1].node, key_name)
        except IndexError:
            start_cursor = None
            end_cursor = None

        # Construct the connection
        return connection_type(
            edges=edges,
            page_info=pageinfo_type(
                start_cursor=start_cursor if start_cursor else '',
                end_cursor=end_cursor if end_cursor else '',
                has_previous_page=has_previous_page,
                has_next_page=has_next
            )
        )

    def get_resolver(self, parent_resolver):
        return partial(self.connection_resolver, parent_resolver, self.type, self.model)

    @classmethod
    def get_edges_from_iterable(cls, iterable, model, edge_type=Edge, after=None, page_size=None):
        edges = []
        count = 0
        has_next = False

        for entity in iterable:
            if after:
                if after != str(getattr(entity, get_key_name(model))):
                    continue
                else:
                    after = False
                    continue
            if page_size and count >= page_size:
                has_next = True
                break
            edges.append(edge_type(node=entity, cursor=entity))
            count += 1

        return [has_next, edges]
