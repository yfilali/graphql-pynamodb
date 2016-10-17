from __future__ import absolute_import

from functools import partial

from graphene import relay
from graphene.relay.connection import PageInfo
from graphql_relay.connection.connectiontypes import Edge


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
        # TODO this is very very basic and needs to handle connection params from args like first, after, etc.
        return model.scan()

    @classmethod
    def connection_resolver(cls, resolver, connection, model, root, args, context, info, **kwargs):
        iterable = resolver(root, args, context, info)
        if iterable is None and len(args):
            iterable = getattr(root, args[0])
        if iterable is None:
            iterable = cls.get_query(model, context, info, args)
        iterable = iter(iterable if iterable is not None else [])
        connection_type = connection
        edge_type = connection.Edge or Edge
        pageinfo_type = PageInfo

        full_args = dict(args, **kwargs)
        first = full_args.get('first')
        after = full_args.get('after')
        has_previous_page = bool(after)
        page_size = first if first else None

        start_cursor = None
        if after:
            for item in iterable:
                if item == after:
                    start_cursor = iterable.next()
                    break

        edges = []
        if page_size:
            while len(edges) < page_size:
                try:
                    entity = iterable.next()
                except StopIteration:
                    break

                edge = edge_type(node=entity, cursor=entity)
                edges.append(edge)
        else:
            edges = [edge_type(node=entity, cursor=entity) for entity in iterable]

        try:
            start_cursor = edges[0].node
            end_cursor = edges[-1].node
        except IndexError:
            end_cursor = None

        try:
            next(iterable)
            has_next = True
        except StopIteration:
            has_next = False

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
