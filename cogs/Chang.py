from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from discord.ext.commands import cog
import requests
import smtplib
import time

class Chang(commands.Cog):
    def __init__(self, client):
	    self.client = client

    @commands.command() 
    async def status(self, ctx, arg): #!status [enter-course-code]
        URL = 'https://continuing.ryerson.ca/search/publicCourseSearchDetails.do?method=load&courseId=' + arg
        page_content = requests.get(URL).text
        soup = BeautifulSoup(page_content,'html.parser')
        await ctx.send(soup.title.string)
        span = soup.findAll('span', {'class' : 'courseProfileSectionAvailability'})
        sections = soup.findAll('span', {'class' : 'sectionCode'})
        for section in sections:
            each_section = section.text.strip()
            for result in span:
                status = result.text.strip()
                if not each_section: #Check if string is empty
                    break
                await ctx.send(f'Section {each_section} is currently {status}!')
                break

    @commands.command() 
    async def monitor(self, ctx, arg, arg2): #!monitor [enter-course-code] [enter-email-address]
        URL = 'https://continuing.ryerson.ca/search/publicCourseSearchDetails.do?method=load&courseId=' + arg
        page_content = requests.get(URL).text
        soup = BeautifulSoup(page_content,'html.parser')
        span = soup.findAll('span', {'class' : 'courseProfileSectionAvailability'})
        found = 0
        while found == 0:
            for result in span:
                status = result.text.strip()
                if status == "Available":
                    await ctx.send(f"Hello {ctx.message.author.mention}, a section has opened up for {soup.title.string.split('|')[0]}")
                    from_address = 'email'
                    to_address = arg2
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login("email", "password")
                    server.sendmail(from_address, to_address, f"Subject: A new section has opened up!\n\nGreetings, a section has opened up for {soup.title.string.split('|')[0]}")
                    found = 1
            if found == 0:
                time.sleep(60)
                continue
        server.quit()

def setup(client):
	client.add_cog(Chang(client))
