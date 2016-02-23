# -*- coding: utf-8 -*-
# data for 2016 allstar voting

from datetime import datetime

ELECTION_DATA = {
    'name': u'2016MAY',
    'description': u'2016台大排球明星賽',
    'start_date': datetime(2016, 4, 1, 8, 0),  # year, month, day, hour, min
    'end_date': datetime(2015, 4, 14, 8, 0),
}
POSITION_DATA = [
    {
        'name': 'setter',
        'description': u'舉球員',
        'votes_per_person': 4,
        'num_elected': 2,
    },
    {
        'name': 'outside',
        'description': u'主攻手',
        'votes_per_person': 8,
        'num_elected': 4,
    },
    {
        'name': 'middle',
        'description': u'攔中手',
        'votes_per_person': 6,
        'num_elected': 3,
    },
    {
        'name': 'rightside',
        'description': u'舉球對角',
        'votes_per_person': 4,
        'num_elected': 2,
    },
    {
        'name': 'libero',
        'description': u'自由球員',
        'votes_per_person': 2,
        'num_elected': 2,
    },
]

