def index_no_except(collection, v):
    try:
        return collection.index(v)
    except:
        return -1
