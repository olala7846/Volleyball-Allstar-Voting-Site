# should be a script that populates election data
from collections import namedtuple

Role = namedtuple('Role', ['name', 'num_votes', 'num_elected'])

ROLES = [
    Role('setter', 4, 2),
    Role('outside', 6, 3),
    Role('middle', 6, 3),
    Role('rightside', 4, 2),
    Role('libero', 4, 2),
]
