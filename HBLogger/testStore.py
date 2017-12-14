import models
import os
from sqlalchemy import create_engine

path = os.path.expanduser("~/.HBLog")
fname = "log.db"
fname = os.path.join(path, fname)
session_maker = models.initialize(fname)
session = session_maker()
ops_list = []

for click in session.query(models.Click).order_by(models.Click.id):
	ops_list.append([click, click.created_at])
for move in session.query(models.Move).order_by(models.Move.id):
	ops_list.append([move, move.created_at])
for idle in session.query(models.Idle).order_by(models.Idle.id):
	ops_list.append([idle, idle.created_at])
for keys in session.query(models.Keys).order_by(models.Keys.id):
	ops_list.append([keys, keys.created_at])

def createTime(list):
	return list[1]
ops_list.sort(key=createTime)
for elem in ops_list:
	print elem[0]
