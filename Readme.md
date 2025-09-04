# Chat Room Application

## This project intends to explore using database notification system to build real time event driven application
In this learning app i wish to test to feasibility of using postgres notify + SSE + redis to create a real time chat room app.

when there is new message sent by user
frontend --send data--> backend --write--> database

when database changes
database --notify--> backend --SSE--> frontend


## Features

- Real-time messaging using Server-Sent Events (SSE)
- Persistent message history
- Using UUID as primary key

## TODO 
- create upload file function
