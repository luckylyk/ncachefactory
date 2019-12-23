
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
