matrix = [
    [1, 2, 3],
    [4, 0, 3],
    [7, 8, 9],
    [0, 3, 0],
    [10, 3, 12]
]

countnozeros = 0
for row in matrix:
    if 0 not in row:
        countnozeros += 1
print("Рядків буз нулів:", countnozeros)

allnumbers = []
for row in matrix:
    for number in row:
        allnumbers.append(number)
counts = {}
for num in allnumbers:
    if num in counts:
        counts[num] += 1
    else:
        counts[num] = 1

maxduplicate = None
for num in counts:
    if counts[num] > 1:
        if maxduplicate is None or num > maxduplicate:
            maxduplicate = num

print("Найбільше повторюване число:", maxduplicate)