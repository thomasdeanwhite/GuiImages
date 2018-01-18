import os, os.path
import random
import string
import cherrypy
import time

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import config
import PyMySQL

def connect_to_db():
    db = PyMySQL.connect(config.db.location, config.db.user, config.db.password, config.db.db)


def init_driver():
    driver = webdriver.Firefox()
    driver.wait = WebDriverWait(driver, 5)
    return driver


def lookup(driver, query):

    try:
        box = driver.wait.until(EC.presence_of_element_located(
            (By.NAME, "q")))
        button = driver.wait.until(EC.element_to_be_clickable(
            (By.NAME, "btnK")))
        box.send_keys(query)
        button.click()

    except TimeoutException:
        print("Box or Button not found in google.com")


def element_to_string(location, size, style_class):
    return "<div class='overlay " + style_class + "' style='left: " + str(location['x']) + "; top: " + str(location['y']) + "; width: " + str(size['width']) + "px; height: " + str(size['height']) + "px;'>&nbsp;</div>"


class StringGenerator(object):
    @cherrypy.expose
    def index(self):
        return open('index.html')

    @cherrypy.expose
    def crawl(self, url="www.google.com"):
        driver = init_driver()
        driver.get("http://" + url)
        #lookup(driver, "Selenium")
        file_name = url.replace(".", "_")
        file_name = file_name.replace("/", "-")
        file = "images/" + file_name + ".png"

        links = driver.find_elements_by_tag_name("a")
        buttons = driver.find_elements_by_tag_name("button")
        text_fields = driver.find_elements_by_tag_name("input")

        webpage = "<html><head><link rel='stylesheet' href='/static/css/style.css'></head><body><img src='static/" + file + "' />"

        for text_field in text_fields:
            field_type = text_field.get_property("type")
            if field_type == "hidden":
                continue

            if field_type == "text" or field_type == "password" or field_type == "email":
                location = text_field.location
                size = text_field.size
                webpage = webpage + element_to_string(location, size, "text_field")
            else:
                print(field_type)
                buttons.append(text_field)

        for link in links:
            location = link.location
            size = link.size
            webpage = webpage + element_to_string(location, size, "link")

        for button in buttons:
            location = button.location
            size = button.size
            webpage = webpage + element_to_string(location, size, "button")

        webpage = webpage + "<p>" + str(len(links)) + " Hyperlinks</p>"
        webpage = webpage + "<p>" + str(len(buttons)) + " Buttons</p>"
        webpage = webpage + "<p>" + str(len(text_fields)) + " Text Fields</p>"

        driver.save_screenshot("public/" + file)
        driver.quit()
        webpage = webpage + "</body></html>"
        return webpage


@cherrypy.expose
class StringGeneratorWebService(object):

    @cherrypy.tools.accept(media='text/plain')
    def GET(self):
        return cherrypy.session['mystring']

    def POST(self, length=8):
        some_string = ''.join(random.sample(string.hexdigits, int(length)))
        cherrypy.session['mystring'] = some_string
        return some_string

    def PUT(self, another_string):
        cherrypy.session['mystring'] = another_string

    def DELETE(self):
        cherrypy.session.pop('mystring', None)


if __name__ == '__main__':
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/manual': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')],
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './public'
        }
    }
    webapp = StringGenerator()
    webapp.manual = StringGeneratorWebService()
    cherrypy.quickstart(webapp, '/', conf)