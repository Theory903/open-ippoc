import timeit

setup = """
processes = {f"proc_{i}": i for i in range(10)}
"""

test_list_keys = """
for name in list(processes.keys()):
    proc = processes[name]
    status = proc
"""

test_items = """
for name, proc in processes.items():
    status = proc
"""

list_keys_time = timeit.timeit(test_list_keys, setup=setup, number=1000000)
items_time = timeit.timeit(test_items, setup=setup, number=1000000)

print(f"list(processes.keys()): {list_keys_time:.4f} seconds")
print(f"processes.items(): {items_time:.4f} seconds")
print(f"Speedup: {list_keys_time / items_time:.2f}x")
