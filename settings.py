# -*- coding: utf-8 -*-
# data for 2016 allstar voting

from datetime import datetime
from candidate_data.role_back import ROLE_BACK
from candidate_data.role_main import ROLE_MAIN
from candidate_data.role_libero import ROLE_LIBERO
from candidate_data.role_setter import ROLE_SETTER
from candidate_data.role_middle import ROLE_MIDDLE

ELECTION_DATA = {
    'title': u'2017台大排球明星賽',
    'description': u'第七屆台大男子排球明星賽',
    # (year, month, day, hour, min) in UTC
    'start_date': datetime(2017, 3, 19, 16, 0),
    'end_date': datetime(2017, 3, 25, 14, 30)
}

POSITION_DATA = [
    {
        'name': 'setter',
        'title': u'舉球員',
        'description': u'舉球員',
        'votes_per_person': 2,
        'num_elected': 4,
        'data': ROLE_SETTER,
    },
    {
        'name': 'outside',
        'title': u'主攻手',
        'description': u'主攻手',
        'votes_per_person': 4,
        'num_elected': 8,
        'data': ROLE_MAIN,
    },
    {
        'name': 'middle',
        'title': u'攔中手',
        'description': u'攔中手',
        'votes_per_person': 3,
        'num_elected': 6,
        'data': ROLE_MIDDLE,
    },
    {
        'name': 'rightside',
        'title': u'輔舉',
        'description': u'輔舉',
        'votes_per_person': 2,
        'num_elected': 4,
        'data': ROLE_BACK,
    },
    {
        'name': 'libero',
        'title': u'自由球員',
        'description': u'自由球員',
        'votes_per_person': 1,
        'num_elected': 2,
        'data': ROLE_LIBERO,
    },
]

