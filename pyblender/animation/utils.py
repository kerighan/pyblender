def assert_list_is_sorted(args):
    assert all(args[i] <= args[i+1] for i in range(len(args)-1))
