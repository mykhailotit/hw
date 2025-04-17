matrix = [
    [0, 0, 0, 0],
    [1, 2, 3, 4],
    [0, 0, 0, 0],
    [5, 0, 6, 0]
]

matrix = [row for row in matrix if any(elem != 0 for elem in row)]
transposed = list(zip(*matrix))
transposed = [col for col in transposed if any(elem != 0 for elem in col)]
compressedmatrix = [list(row) for row in zip(*transposed)]

print("Стиснена матриця:")
for row in compressedmatrix:
    print(row)

firstpositiverowindex = -1
for i, row in enumerate(compressedmatrix):
    for value in row:
        if value > 0:
            firstpositiverowindex = i
            break
    if firstpositiverowindex != -1:
        break

print("№ строки з хоча б одним додатнім елементом:", firstpositiverowindex)