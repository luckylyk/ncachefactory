

def compute_wedging_values(start_value, end_value, iterations):
    """
    This function create a list of values with linear interpolation.
    """
    if iterations < 3:
        return start_value, end_value
    iterations -= 2
    difference = float(abs(end_value - start_value))
    iteration_value = difference / (iterations + 1)
    return [start_value + (i * iteration_value) for i in range(iterations + 2)]


def overlap_arrays_from_ranges(arrays, ranges):
    """
    This function receive arrays and their range. returns the arrays
    overlapped with a None value added to the created indexes.
    e.g. array1 = (2, 3, 8), range1 = (2, 4), array2 = (True, 'Lio', False),
    range2 = (1, 3).
    result = array1: (None, 2, 3, 8), array2: (True, 'Lio', False, None)
    """
    msg = "this function has to receive the same number of arrays and ranges"
    assert len(arrays) == len(ranges), msg
    ranges = normalize_ranges(ranges)
    dicts = []
    for array, range_ in zip(arrays, ranges):
        dict_ = {i: p for i, p in zip(range(range_[0], range_[1] + 1), array)}
        dicts.append(dict_)
    arrays = [[] for _ in range(len(arrays))]
    range_end = max([r[-1] for r in ranges])
    for i in range(range_end):
        for j, array in enumerate(arrays):
            array.append(dicts[j].get(i))
    return arrays


def range_ranges(ranges):
    """
    Return int array generated starting on the smallest range start to the
    highest range end.
    """
    ranges = [n for r in ranges for n in range(r[0], r[-1] + 1)]
    return sorted(list(set(ranges)))


def normalize_ranges(ranges):
    """
    This function compare several ranges and offset the relative start
    to 0. If the ranges has a gap, for example, range1 finish to 50 and
    range2 start at 65. The gap is removed.
    """
    offset = sorted(ranges)[0][0]
    ranges = [[n - offset for n in r] for r in ranges]
    has_gap = []
    # offset all the range to 0 as reference
    for i, range_ in enumerate(ranges):
        values = [r[1] for r in ranges if r[0] < range_[0]]
        if not values:
            continue
        if max(values) < range_[0]:
            offset = range_[0] - max(values)
            has_gap.append((offset, i))
    # remove the gap between the ranges
    global_offset = 0
    for offset, i in sorted(has_gap):
        global_offset += offset - 1
        ranges[i] = [n - global_offset for n in ranges[i]]
    return ranges
