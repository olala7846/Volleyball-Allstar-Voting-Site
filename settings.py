# -*- coding: utf-8 -*-
# data for 2016 allstar voting

from datetime import datetime

ELECTION_DATA = {
    'name': u'2016MAY',
    'title': u'2016排球明星賽',
    'description': u'2016台大排球明星賽',
    'start_date': datetime(2016, 4, 1, 8, 0),  # year, month, day, hour, min
    'end_date': datetime(2015, 4, 14, 8, 0),
    'finished': False,
}
POSITION_DATA = [
    {
        'name': 'setter',
        'title': u'舉球員',
        'description': u'舉球員',
        'votes_per_person': 4,
        'num_elected': 2,
    },
    {
        'name': 'outside',
        'title': u'主攻手',
        'description': u'主攻手',
        'votes_per_person': 8,
        'num_elected': 4,
    },
    {
        'name': 'middle',
        'title': u'攔中手',
        'description': u'攔中手',
        'votes_per_person': 6,
        'num_elected': 3,
    },
    {
        'name': 'rightside',
        'title': u'舉球對角',
        'description': u'舉球對角',
        'votes_per_person': 4,
        'num_elected': 2,
    },
    {
        'name': 'libero',
        'title': u'自由球員',
        'description': u'自由球員',
        'votes_per_person': 2,
        'num_elected': 2,
    },
]

