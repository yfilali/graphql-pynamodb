def get_query(model, context):
    query = getattr(model, 'scan', None)
    if not query:
        raise Exception('A query in the model Base is required for querying.\n'
                        'Read more http://pynamodb.readthedocs.io/en/latest/quickstart.html?highlight=query#querying')
    return query
