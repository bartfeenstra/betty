import gc
import multiprocessing
import pickle
from multiprocessing.managers import DictProxy

# if __name__ == "__main__":
#     proxy = multiprocessing.Manager().dict()
#     pickled_proxy = pickle.dumps(proxy)
#
#     proxy2 = pickle.loads(pickled_proxy)
#     pickled_proxy2 = pickle.dumps(proxy2)
#     # Garbage-collecting `proxy` causes a FileNotFoundError in multiprocessing's socket connection.
#     # I would have expected that at this time, `proxy` and `proxy2` both refer to the same referent,
#     # and one of them should be safely removable.
#
#     proxy3 = pickle.loads(pickled_proxy2)
#     # If we instead `del proxy` and garbage-collect here, the code completes successfully.
#     pickled_proxy3 = pickle.dumps(proxy3)
#     del proxy
#     gc.collect()
#
#     proxy4 = pickle.loads(pickled_proxy3)
#     assert isinstance(proxy4, DictProxy)

if __name__ == "__main__":
    proxy = pickle.loads(pickle.dumps(multiprocessing.Manager().dict()))
    assert isinstance(proxy, DictProxy)
