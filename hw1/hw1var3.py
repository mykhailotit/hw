matrix = [
    [1, 0, 5, 4],
    [0, 0, 3, 3],
    [3, 3, 3, 0],
    [5, 6, 3, 4]
]

columnswithzero = 0
for col in range(len(matrix[0])):
    for row in range(len(matrix)):
        if matrix[row][col] == 0:
            columnswithzero += 1
            break
print("Стовпців з нулем:", columnswithzero)

maxserieslength = 0
rowmaxseries = -1

for i in range(len(matrix)):
    currentlength = 1
    maxlengthinrow = 1
    for j in range(1, len(matrix[i])):
        if matrix[i][j] == matrix[i][j - 1]:
            currentlength += 1
            if currentlength > maxlengthinrow:
                maxlengthinrow = currentlength
        else:
            currentlength = 1
    if maxlengthinrow > maxserieslength:
        maxserieslength = maxlengthinrow
        rowmaxseries = i

print("Рядок з найдовшою серією однакових елементів:", rowmaxseries)