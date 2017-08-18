import models
from sqlalchemy import create_engine

session_maker = models.initialize("log.db")
session = session_maker()

for click in session.query(models.Click).order_by(models.Click.id):
     print click
for move in session.query(models.Move).order_by(models.Move.id):
     print move
for idle in session.query(models.Idle).order_by(models.Idle.id):
     print idle
for ditrigraph in session.query(models.Ditrigraph).order_by(models.Ditrigraph.id):
     print ditrigraph
for keys in session.query(models.Keys).order_by(models.Keys.id):
     print keys