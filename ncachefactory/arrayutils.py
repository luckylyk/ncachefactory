
def overlap_lists_from_ranges(elements1, elements2, range1, range2):
    """ TODO important docstring to write. This shit MUST be explained """
    range1, range2 = normalize_ranges(range1, range2)
    dict1 = {i: p for i, p in zip(range(range1[0], range1[1] + 1), elements1)}
    dict2 = {i: p for i, p in zip(range(range2[0], range2[1] + 1), elements2)}
    list1 = []
    list2 = []
    range_end = max(range1[-1], range2[-1])
    for i in range(range_end):
        list1.append(dict1.get(i))
        list2.append(dict2.get(i))
    return list1, list2


def range_ranges(range1, range2):
    """ TODO important docstring to write. This shit MUST be explained """
    beginner_range, second_range = sorted([range1, range2])
    if beginner_range[-1] >= second_range[0]:
        end_range = max([beginner_range[-1], second_range[-1]])
        return [n for n in range(beginner_range[0], end_range + 1)]
    range1 = [n for n in range(beginner_range[0], beginner_range[1] + 1)]
    range2 = [n for n in range(second_range[0], second_range[1] + 1)]
    return range1 + range2


def normalize_ranges(range1, range2):
    """ TODO important docstring to write. This shit MUST be explained """
    revert_return = range1[0] > range2[0]
    beginner_range, second_range = sorted([range1, range2])
    offset = beginner_range[0]
    range1 = [n - offset for n in beginner_range]
    range2 = [n - offset for n in second_range]
    if range1[-1] >= range2[0]:
        if revert_return:
            return range2, range1
        return range1, range2
    offset = range2[0] - range1[-1]
    range2 = [n - offset + 1 for n in range2]
    if revert_return:
        return range2, range1
    return range1, range2


if __name__ == '__main__':
    # those sensitive abstract functions needs to be tested after every
    # edit. Ensure those tests are passed with success before push a change.
    assert range_ranges([0, 10], [5, 15]) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    assert range_ranges([0, 5], [10, 15]) == [0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15]
    assert range_ranges([5, 15], [0, 10]) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    assert range_ranges([10, 15], [0, 5]) == [0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15]
    assert range_ranges([5, 15], [0, 10]) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    assert range_ranges([10, 15], [0, 5]) == [0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15]
    assert normalize_ranges([50, 100], [50, 100]) == ([0, 50], [0, 50])
    assert normalize_ranges([50, 100], [70, 120]) == ([0, 50], [20, 70])
    assert normalize_ranges([50, 90], [100, 110]) == ([0, 40], [41, 51])
    assert normalize_ranges([100, 110], [50, 90]) == ([41, 51], [0, 40])
    assert normalize_ranges([20, 40], [50, 65]) == ([0, 20], [21, 36])
    assert normalize_ranges([50, 65], [20, 40]) == ([21, 36], [0, 20])
    assert normalize_ranges([0, 100], [20, 40]) == ([0, 100], [20, 40])
    assert normalize_ranges([50, 150], [70, 90]) == ([0, 100], [20, 40])
    assert normalize_ranges([20, 40], [0, 100]) == ([20, 40], [0, 100])
    assert normalize_ranges([70, 90], [50, 150]) == ([20, 40], [0, 100])
    range1 = [20, 40]
    range2 = [50, 65]
    elements1 = [True for _ in range(range1[0], range1[1] + 1)]
    elements2 = [True for _ in range(range2[0], range2[1] + 1)]
    result = overlap_lists_from_ranges(elements1, elements2, range1, range2)
    assert result == ([
        True, True, True, True, True, True, True, True, True, True, True, True,
        True, True, True, True, True, True, True, True, True, None, None, None,
        None, None, None, None, None, None, None, None, None, None, None, None],[
        None, None, None, None, None, None, None, None, None, None, None, None,
        None, None, None, None, None, None, None, None, None, True, True, True,
        True, True, True, True, True, True, True, True, True, True, True, True])