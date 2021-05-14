import discord
import firebase_admin
import os.path
from discord.ext import commands
from discord.ext.commands import cog
from datetime import datetime
from firebase_admin import credentials
from firebase_admin import firestore
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Reminder Notification System
class Reminder(commands.Cog):
    sortType = "NORMAL"
    try:
        cred = credentials.Certificate('./serviceAccount.json')
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase has launched")
    except:
        print("Firebase failed to launch")

    def __init__(self, client):
	    self.client = client

    @commands.command() 
    async def addTask(self, ctx, taskName, taskType, taskDueDate): #!addTask [task-name] [task-type] [due-date] (Use Quotes for Task Name)
        # Example: !addTask "Lab 6" COE428 02/04/2021 (Month/Day/Year)
        data = {
            u'name': taskName,
            u'type': taskType,
            u'dueDate': taskDueDate
        }
        self.db.collection(u'users').document(str(ctx.author.id)).collection(u'tasks').add(data)

    @commands.command() 
    async def displayTasks(self, ctx): #!displayTasks
        embed = discord.Embed(title="Tasks", description=f"Welcome { ctx.author }, Here is your Task List!")
        tasks = self.db.collection(u'users').document(str(ctx.author.id)).collection(u'tasks').stream()
        tasksDict = []
        for task in tasks:
            tasksDict.append(task.to_dict())

        taskName, taskType, taskDueDate = "", "", ""
        for task in tasksDict:
            taskName += task['name'] + "\n"
            taskType += task['type'] + "\n"
            taskDueDate += task['dueDate'] + "\n"

        embed.add_field(name="Task Name", value=taskName, inline=True)
        embed.add_field(name="Type", value=taskType, inline=True)
        embed.add_field(name="Due Date", value=taskDueDate, inline=True)
        message = await ctx.send(embed=embed)
        await message.add_reaction("\N{REGIONAL INDICATOR SYMBOL LETTER N}")
        await message.add_reaction("\N{REGIONAL INDICATOR SYMBOL LETTER T}")
        await message.add_reaction("\N{REGIONAL INDICATOR SYMBOL LETTER D}")
        
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user): #Sorting has 3 options: Date Added (Default), Type, Due-Date
        sortType = "NORMAL"
        if user.id == 704529961867935744: return
        emoji = reaction.emoji
        if emoji == "\N{REGIONAL INDICATOR SYMBOL LETTER N}":
            self.sortType = "NORMAL"
        elif emoji == "\N{REGIONAL INDICATOR SYMBOL LETTER T}":
            self.sortType = "TYPE"
        elif emoji == "\N{REGIONAL INDICATOR SYMBOL LETTER D}":
            self.sortType = "DUE_DATE"
        
        sortedEmbed = discord.Embed(title="Tasks", description=f"Welcome { user.name }, Here is your Task List!")
        if self.sortType == "NORMAL":
            tasks = self.db.collection(u'users').document(str(user.id)).collection(u'tasks').stream()
        elif self.sortType == "TYPE":
            tasks = self.db.collection(u'users').document(str(user.id)).collection(u'tasks').order_by(u'type').stream()
        elif self.sortType == "DUE_DATE":
            tasks = self.db.collection(u'users').document(str(user.id)).collection(u'tasks').order_by(u'dueDate').stream()

        tasksDict = []
        for task in tasks:
            tasksDict.append(task.to_dict())

        taskName, taskType, taskDueDate = "", "", ""
        for task in tasksDict:
            taskName += task['name'] + "\n"
            taskType += task['type'] + "\n"
            taskDueDate += task['dueDate'] + "\n"

        sortedEmbed.add_field(name="Task Name", value=taskName, inline=True)
        sortedEmbed.add_field(name="Type", value=taskType, inline=True)
        sortedEmbed.add_field(name="Due Date", value=taskDueDate, inline=True)
        await reaction.message.edit(embed=sortedEmbed)

    @commands.command()
    async def deleteTask(self, ctx, taskID): #!deleteTask [taskID]
        if int(taskID) < 1: return
        if self.sortType == "NORMAL":
            tasks = self.db.collection(u'users').document(str(ctx.author.id)).collection(u'tasks')
        elif self.sortType == "TYPE":
            tasks = self.db.collection(u'users').document(str(ctx.author.id)).collection(u'tasks').order_by(u'type')
        elif self.sortType == "DUE_DATE":
            tasks = self.db.collection(u'users').document(str(ctx.author.id)).collection(u'tasks').order_by(u'dueDate')
        tasksDict = []
        taskIDs = []
        for task in tasks.stream():
            tasksDict.append(task.to_dict())
            taskIDs.append(task.id)
        taskName = tasksDict[int(taskID) - 1]['name']
        tasks.document(str(taskIDs[int(taskID) - 1])).delete()

    @commands.command() 
    async def addReminder(self, ctx, taskID, taskRD, taskRT): #!addReminder [taskID] [Date] [Time in 24h Clock]
        # Example: !addReminder 1 05/06/2021 16:00
        if int(taskID) < 1:
            await ctx.send("Invalid Task ID")
            return
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=5000)

        service = build('calendar', 'v3', credentials=creds)

        # Month/Day/Year Hours:Minutes
        date_string = taskRD + " " + taskRT
        date_iso = datetime.strptime(date_string, "%m/%d/%Y %H:%M").isoformat()
        print(date_iso)

        tasks = self.db.collection(u'users').document(str(ctx.author.id)).collection(u'tasks').stream()
        tasksDict = []
        for task in tasks:
            tasksDict.append(task.to_dict())

        event = {
            'summary': f"Reminder for Task #{taskID}, {tasksDict[int(taskID) - 1]['name']}",
            'description': f"Friendly Reminder: Task #{taskID} is due on: {tasksDict[int(taskID) - 1]['dueDate']}!",
            'start': {
                'dateTime': date_iso,
                'timeZone': 'America/Toronto',
            },
            'end': {
                'dateTime': date_iso,
                'timeZone': 'America/Toronto',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        embed = discord.Embed(title="Reminder Created!", description=f"Hi { ctx.author }, your Reminder has been successfully created!")
        embed.add_field(name="Event Link:", value=event.get('htmlLink'), inline=False)
        await ctx.send(embed=embed)

def setup(client):
    client.add_cog(Reminder(client))
