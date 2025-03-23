## This project intends to explore using database notification system to build real time event driven application

I intend to use pg_notify or debezium to listen to database changes to build real time chat room app

when there is new message sent by user
frontend --send data--> backend --write--> database

when database changes
database --notify--> backend --SSE--> frontend