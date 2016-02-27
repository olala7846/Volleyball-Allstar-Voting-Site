#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re


def is_start_line_of_new_role(line):
    m = re.search("[1-9][0-9]{0,1}\..*", line)
    if m:
        return True
    else:
        return False


def strip_title_number(line):
    m = re.search("[1-9][0-9]{0,1}\.", line)
    if m:
        numstr = m.group()
        return line.strip(numstr)
    else:
        print "ERROR"
        return "ERROR"


def parse_file(type):
    filename = 'role_%s.txt' % type
    fp = open(filename)
    role_title = ""
    role_description = ""
    for line in fp.readlines():
        if is_start_line_of_new_role(line):
            #print role data
            print role_title+"#"+role_description
            #reset role descrition and title
            role_description = ""
            role_title = strip_title_number(line.strip())
        else:
            role_description += line.strip()
            role_description += "<br>"
    print role_title+"#"+role_description

parse_file('main')
