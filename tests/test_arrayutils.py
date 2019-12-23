from ncachefactory.arrayutils import range_ranges, normalize_ranges

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