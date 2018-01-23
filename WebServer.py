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
import pymysql

testing_percent = 0.02
validation_percent = 0.005

def connect_to_db():
    db = pymysql.connect(config.db['location'], config.db['user'], config.db['password'], config.db['db'])
    return db

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


def dims_to_relative(body_width, body_height, location, size):
    return {
        'xmin':max((location['x']/body_width), -0.1),
        'xmax':min(((location['x']+size['width'])/body_width), 1.1),
        'ymin':max((location['y']/body_height), -0.1),
        'ymax':min(((location['y']+size['height'])/body_height), 1.1),
    }


def element_to_string(location, size, body_width, body_height, style_class):
    label_info = dims_to_relative(body_width, body_height, location, size)

    # filter elements not on the screen:
    if label_info['xmin'] > 1 or label_info['ymin'] > 1 or label_info['xmax'] < 0 or label_info['ymax'] < 0:
        return None

    return {
        'contents':"<div class='overlay " + style_class + "' style='left: " + str(int(label_info['xmin']*body_width)) + "; top: " + str(int(label_info['ymin']*body_height)) + "; width: " + str(int((label_info['xmax']-label_info['xmin'])*body_width-4)) + "px; height: " + str(int((label_info['ymax']-label_info['ymin'])*body_height-4)) + "px;'>&nbsp;</div>",
        'dims':label_info,
    }

def get_label(element, tag, body_width, body_height):
    location = element.location
    size = element.size
    label = element_to_string(location, size, body_width, body_height, tag)
    return label

def insert_label(cursor, db, image_id, dims, label_type):
    existing = None

    sql = "SELECT * FROM label_types \
               WHERE LabelName = '%s'" % (label_type)

    try:
        # Execute the SQL command
        cursor.execute(sql)
        # Fetch all the rows in a list of lists.
        results = cursor.fetchall()
        for row in results:
            existing = row
    except:
        print ("Error: unable to fetch data")

    label_id = -1
    if existing == None:
        insert_label = "INSERT INTO label_types(LabelName) VALUES ('%s')" % (label_type)

        try:
            cursor.execute(insert_label)
            db.commit()
        except pymysql.InternalError as e:
            print(e)
            db.rollback()

        label_id = db.insert_id()
    else:
        label_id = existing[0]

    truncated = 0
    if dims['xmin'] < 0 or dims['xmax'] > 1 or dims['ymin'] < 0 or dims['ymax'] > 1:
        truncated = 1
        dims['xmin'] = max(0, dims['xmin'])
        dims['xmax'] = min(1, dims['xmax'])
        dims['ymin'] = max(0, dims['ymin'])
        dims['ymax'] = min(1, dims['ymax'])

    insert_label = "INSERT INTO labels(Source, Confidence, ImageId, XMin, XMax, YMin, YMax, IsTruncated, LabelType) VALUES ('%s', '%f', '%d', '%f', '%f', '%f', '%f', '%d', '%d')" % ("unverified", 0.0, image_id, dims['xmin'], dims['xmax'], dims['ymin'], dims['ymax'], truncated, label_id)
    try:
        cursor.execute(insert_label)
        db.commit()
    except pymysql.InternalError as e:
        print(e)
        db.rollback()


class StringGenerator(object):
    @cherrypy.expose
    def index(self):
        return open('index.html')

    @cherrypy.expose
    def crawl(self, url="www.google.com"):
        db = connect_to_db()
        file_name = url.replace(".", "_")
        file_name = file_name.replace("/", "-")
        file_name = file_name.replace("\"", "&quote")
        file_name = file_name.replace("'", "&apos")
        file = "images/" + file_name + ".png"

        cursor = db.cursor()

        sql = "SELECT * FROM images \
               WHERE File = '%s'" % (file)

        existing = None
        try:
            # Execute the SQL command
            cursor.execute(sql)
            # Fetch all the rows in a list of lists.
            results = cursor.fetchall()
            for row in results:
                existing = row
        except pymysql.InternalError as e:
            print (e)
        webpage = "<html><head><link rel='stylesheet' href='/static/css/style.css'></head><body><img src='static/" + file + "' />"
        if existing == None:
            driver = init_driver()
            driver.get("http://" + url)

            dataset = "train"
            random_num = random.random()
            if random_num < validation_percent: # this gets assigned to validation
                dataset = "validate"
            elif random_num < validation_percent + testing_percent: #assigned to training
                dataset = "test"

            body = driver.find_element_by_tag_name("body")

            body_width=body.size['width']
            body_height=body.size['height']

            client_width=driver.execute_script("return document.documentElement.clientWidth")

            if body_width <= 0:
                body_width = client_width
            elif client_width > 0:
                body_width = min(client_width, body_width)

            client_height=driver.execute_script("return document.documentElement.clientHeight")

            if body_height <= 0:
                body_height = client_height
            elif client_height > 0:
                body_height = min(client_height, body_height)

            insert_img = "INSERT INTO images(Subset, File, Width, Height) VALUES ('%s', '%s', '%d', '%d')" % (dataset, file,
                                                                                                              body_width, body_height)

            try:
                cursor.execute(insert_img)
                db.commit()
            except pymysql.InternalError as e:
                print(e)
                db.rollback()

            image_id = cursor.lastrowid

            links = driver.find_elements_by_tag_name("a")
            buttons = driver.find_elements_by_tag_name("button")
            text_fields = driver.find_elements_by_tag_name("input")



            for text_field in text_fields:

                field_type = text_field.get_property("type")
                if field_type == "hidden" or not text_field.is_displayed():
                    continue

                if field_type == "text" or field_type == "password" or field_type == "email":
                    label = get_label(text_field, "text_field", body_width, body_height)
                    if label == None:
                        continue
                    webpage = webpage + label['contents']
                    insert_label(cursor, db, image_id, label['dims'], 'text_field')
                else:
                    buttons.append(text_field)

            for link in links:
                if not link.is_displayed():
                    continue
                label = get_label(link, "link", body_width, body_height)
                if label == None:
                    continue
                webpage = webpage + label['contents']
                insert_label(cursor, db, image_id, label['dims'], 'hyperlink')

            for button in buttons:
                if not button.is_displayed():
                    continue
                label = get_label(button, "button", body_width, body_height)
                if label == None:
                    continue
                webpage = webpage + label['contents']
                insert_label(cursor, db, image_id, label['dims'], 'button')

            driver.save_screenshot("public/" + file)
            driver.quit()
        else:
            #Do stuff when image already exists (validate an unvalidated single box?)
            webpage = webpage + "<h1>This image exists</h1>"
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