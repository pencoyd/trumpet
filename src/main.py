#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
import os
import logging
from google.appengine.ext.webapp import template
from src.models import AudioFile, Station
from django.utils import simplejson

from datetime import datetime, timedelta,date


class MainHandler(webapp.RequestHandler):
    def render(self, template_file, template_values = {}):
       path = os.path.join(os.path.dirname(__file__)[:-4], 'templates', template_file)
       self.response.out.write(template.render(path, template_values))

    def get(self):
        self.render("index.html")

class FileJson(webapp.RequestHandler):

    def get(self):
        playlist=[]
        stationid=self.request.get("stationid",None)
        query = db.Query(AudioFile)
        day=self.request.get("day",date.today())
        day = datetime(day.year, day.month, day.day)
        created_start = day-timedelta(days=7)
        created_end = day + timedelta(days=1)
        query.filter('published >=', created_start)
        query.filter('published <', created_end)
        logging.info(created_start)
        logging.info(created_end)
        if stationid is not None:
            station = Station.get_by_id(long(stationid))
            query.filter("feed IN",station.feeds)
        query.order('-published')
        files = query.fetch(limit=50)
        for item in files:
            playlist.append({"name":str(item.title),"mp3":str(item.url),"date":item.published.strftime("%b %d %Y")})
        self.response.out.write(simplejson.dumps(playlist))


class StationHandler(webapp.RequestHandler):
    def render(self, template_file, template_values = {}):
       path = os.path.join(os.path.dirname(__file__), 'templates', template_file)
       self.response.out.write(template.render(path, template_values))
    def get(self,station):
        if station == "":
            self.redirect('/')
        station = Station.get_by_id(long(station))
        playlist=[]
        feeds ={}
        for feed in station.feeds:
            feed = db.get(feed)
            feeds[str(feed.key())]=str(feed.title)
        self.render("station.html",template_values={"files":{},"feeds":feeds.__repr__(),"stationname":station.title,"stationid":station.key().id()})
    def post(self,station):
        station = Station.get_by_id(long(station))
        feed = self.request.get("feed",None)
        if feed is not None:
            feed = db.get(feed)
            station.feeds.append(feed)



class StationJson(webapp.RequestHandler):
    def get(self):
        shows={}
        for show in Station.all().order("-title").fetch(limit=25):
            shows[str(show.key().id())]=str(show.title)
        self.response.out.write(simplejson.dumps(shows))

    def post(self):
        stationname = self.request.get("station",None)
        if stationname is not None:
            station = Station()
            station.title = stationname
            station.put()
        self.response.out.write(simplejson.dumps({str(station.key().id()):str(station.title)}))

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                           ('/s/([^/]+)?', StationHandler), 
                                          ('/json/stations', StationJson),
                                          ('/json/files', FileJson),],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
