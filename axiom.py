import itertools

somelists = [
   [1, 2, 3],
   ['a', 'b'],
   [4, 5]
]

for element in itertools.product(*somelists):
    print(element)
