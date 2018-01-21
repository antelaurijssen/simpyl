test = [1, 2, 3, 4]
test2 = []
for i in test:
    if i != test[0]:
        test[0] = i
        test2.append(test)
        print test2
