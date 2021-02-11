import os.path
import sqlite3
import chromedriver_autoinstaller
import schedule
import re
import codecs

from time import sleep
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys


class Bot:
    URL = 'https://teams.microsoft.com'

    def __init__(self, email, password, incorrect_creds, ):
        self.email = email
        self.password = password
        self.incorrect_creds = incorrect_creds

    def validate_input(self, regex, text):
        if not re.match(regex, text):
            return False
        return True

    def validate_day(self, day):
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        if day.lower() in days:
            return True
        return False

    def login(self):
        sleep(2)
        email_input = self.browser.find_element_by_id('i0116')
        email_input.send_keys(self.email)
        email_input.send_keys(Keys.ENTER)
        sleep(2)

        password_input = self.browser.find_element_by_id('i0118')
        password_input.send_keys(self.password)
        password_input.send_keys(Keys.ENTER)
        sleep(2)

        try:
            self.browser.find_element_by_id('passwordError')
            self.incorrect_creds()
            return
        except:
            pass

        try:
            self.browser.find_element_by_id('usernameError')
            self.incorrect_creds()
            return
        except:
            pass

        try:
            self.browser.find_element_by_id('idTD_Error')
            print('--- To many incorrect logins (Try later) --- ')
            self.incorrect_creds()
            return
        except:
            pass

        submit = self.browser.find_element_by_id('idSIButton9')
        submit.click()

    def create_db(self):
        conn = sqlite3.connect('teams.db')
        c = conn.cursor()

        # Create table
        try:
            c.execute('CREATE TABLE lessons(class text, start_time text, end_time text, day text)')
        except:
            print('Database already exists')

        conn.commit()
        conn.close()

    def show_db(self):
        print('-' * 25)
        print('\nYOUR TEAMS LESSONS:')

        conn = sqlite3.connect('teams.db')
        c = conn.cursor()
        for row in c.execute('SELECT * FROM lessons'):
            print(row)
        conn.close()

        print('-' * 25)

    def add_lesson(self):
        op = int(input("1. Add class\n2. Done adding\nEnter option : "))

        while(op == 1):
            name = input('Enter class name : ')
            start_time = input('Enter class start time in 24 hour format: (HH:MM) ')
            while not(self.validate_input('\d\d:\d\d', start_time)):
                print('Invalid input, try again')
                start_time = input('Enter class start time in 24 hour format: (HH:MM) ')

            end_time = input('Enter class end time in 24 hour format: (HH: MM) ')
            while not(self.validate_input('\d\d:\d\d', end_time)):
                print('Invalid input, try again')
                end_time = input('Enter class end time in 24 hour format: (HH:MM) ')

            day = input('Enter day (Monday/Tuesday/Wednesday..etc) : ')
            while not(self.validate_day(day.strip())):
                print('Invalid input, try again')
                end_time = input('Enter day (Monday/Tuesday/Wednesday..etc) : ')

            conn = sqlite3.connect('teams.db')
            c = conn.cursor()

            # Insert a row of data
            c.execute("INSERT INTO lessons VALUES ('%s','%s','%s','%s')" % (name, start_time, end_time, day))

            conn.commit()
            conn.close()

            print("Class added to database\n")

            op = int(input("1. Add class\n2. Done adding\nEnter option : "))

    def join_lesson(self, class_name, start_time, end_time):
        print('--- Waiting for classes ---')

        sleep(5)

        classes_available = self.browser.find_elements_by_class_name("name-channel-type")

        for i in classes_available:
            if class_name.lower() in i.get_attribute('innerHTML').lower():
                print("JOINING CLASS ", class_name)
                i.click()
                break

        sleep(4)

        try:
            joinbtn = self.browser.find_element_by_class_name("ts-calling-join-button")
            joinbtn.click()

        except:
            # join button not found
            # refresh every minute until found
            k = 1
            while(k <= 15):
                print("Join button not found, trying again")
                sleep(60)
                self.browser.refresh()
                self.join_lesson(class_name, start_time, end_time)
                # schedule.every(1).minutes.do(joinclass,class_name,start_time,end_time)
                k += 1
            print("Seems like there is no class today.")

        sleep(4)
        webcam = self.browser.find_element_by_xpath(
            '//*[@id="page-content-wrapper"]/div[1]/div/calling-pre-join-screen/div/div/div[2]/div[1]/div[2]/div/div/section/div[2]/toggle-button[1]/div/button')
        if(webcam.get_attribute('aria-pressed') == 'true'):
            webcam.click()
        sleep(1)

        microphone = self.browser.find_element_by_xpath('//*[@id="preJoinAudioButton"]/div/button')
        if(microphone.get_attribute('aria-pressed') == 'true'):
            microphone.click()

        sleep(1)
        joinnowbtn = self.browser.find_element_by_xpath(
            '//*[@id="page-content-wrapper"]/div[1]/div/calling-pre-join-screen/div/div/div[2]/div[1]/div[2]/div/div/section/div[1]/div/div/button')
        joinnowbtn.click()

        # now schedule leaving class
        tmp = "%H:%M"

        class_running_time = datetime.strptime(end_time, tmp) - datetime.strptime(start_time, tmp)

        sleep(class_running_time.seconds)

        self.browser.find_element_by_class_name("ts-calling-screen").click()

        self.browser.find_element_by_xpath('//*[@id="teams-app-bar"]/ul/li[3]').click()  # come back to homepage
        sleep(1)

        self.browser.find_element_by_xpath('//*[@id="hangup-button"]').click()
        print("Class left")

    def sched(self):
        conn = sqlite3.connect('teams.db')
        c = conn.cursor()
        for row in c.execute('SELECT * FROM lessons'):
            # schedule all classes
            name = row[0]
            start_time = row[1]
            end_time = row[2]
            day = row[3]

            if day.lower() == "monday":
                schedule.every().monday.at(start_time).do(self.join_lesson, name, start_time, end_time)
                print("Scheduled class '%s' on %s at %s" % (name, day, start_time))

            if day.lower() == "tuesday":
                schedule.every().tuesday.at(start_time).do(self.join_lesson, name, start_time, end_time)
                print("Scheduled class '%s' on %s at %s" % (name, day, start_time))

            if day.lower() == "wednesday":
                schedule.every().wednesday.at(start_time).do(self.join_lesson, name, start_time, end_time)
                print("Scheduled class '%s' on %s at %s" % (name, day, start_time))

            if day.lower() == "thursday":
                schedule.every().thursday.at(start_time).do(self.join_lesson, name, start_time, end_time)
                print("Scheduled class '%s' on %s at %s" % (name, day, start_time))

            if day.lower() == "friday":
                schedule.every().friday.at(start_time).do(self.join_lesson, name, start_time, end_time)
                print("Scheduled class '%s' on %s at %s" % (name, day, start_time))

            if day.lower() == "saturday":
                schedule.every().saturday.at(start_time).do(self.join_lesson, name, start_time, end_time)
                print("Scheduled class '%s' on %s at %s" % (name, day, start_time))

            if day.lower() == "sunday":
                schedule.every().sunday.at(start_time).do(self.join_lesson, name, start_time, end_time)
                print("Scheduled class '%s' on %s at %s" % (name, day, start_time))

        # Start browser
        self.start_bot()
        while True:
            # Checks whether a scheduled task
            # is pending to run or not
            schedule.run_pending()
            sleep(1)

    def start_bot(self):
        opt = Options()
        opt.add_argument("--disable-infobars")
        opt.add_argument("start-maximized")
        opt.add_argument("--disable-extensions")
        opt.add_argument("--start-maximized")
        # Pass the argument 1 to allow and 2 to block
        opt.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.geolocation": 1,
            "profile.default_content_setting_values.notifications": 1
        })

        chromedriver_autoinstaller.install()
        self.browser = webdriver.Chrome(options=opt)
        self.browser.get(self.URL)

        WebDriverWait(self.browser, 10000).until(EC.visibility_of_element_located((By.TAG_NAME, 'body')))

        if("login.microsoftonline.com" in self.browser.current_url):
            self.login()

    def start(self):
        if not(os.path.isfile('teams.db')):
            print('--- Creating Database ---')
            self.create_db()
            print('--- Database Created')
        sleep(2)

        while True:
            print('\n1 - Start Bot')
            print('2 - Add Lesson')
            print('3 - Show Lesson Table')
            action = input('\nWhat do you want to do? : ')

            # Start Bot
            if action == '1':
                self.sched()

            # Add lesson
            elif action == '2':
                self.add_lesson()

            # Show Database
            elif action == '3':
                self.show_db()

            # Wrong choice
            else:
                print('\n--- Wrong choice ---')


if __name__ == '__main__':
    # Create folder if doesn't exist yet
    if not(os.path.exists(r'C:\Teams Bot')):
        os.makedirs(r'C:\Teams Bot')

    # Get email and passowrd to the lingos from login.txt
    while True:
        try:
            with codecs.open(r'C:\Teams Bot\login.txt', 'r', 'utf-8') as f:
                file = f.readline().split(',')
                EMAIL = file[0]
                PASSWORD = file[1]
        except:
            # Create a login.txt if doesn't exist
            with codecs.open(r'C:\Teams Bot\login.txt', 'w', 'utf-8') as f:
                while True:
                    EMAIL = str(input('Your email: '))
                    correct_email = str(input('Confirm email: '))

                    if not(EMAIL == correct_email):
                        print('\a\n--- Emails are not the same ---\n')
                        continue
                    break  # if emails are correct then break
                print('\n')

                while True:
                    PASSWORD = str(input('Your password: '))
                    correct_password = str(input('Confirm password: '))

                    if not(PASSWORD == correct_password):
                        print('\a\n--- Passwords are not the same ---\n')
                        continue
                    break  # If passwords are correct then break

                f.write(f'{EMAIL},{PASSWORD}')  # Save login
                continue

        # Start a Bot

        def incorrect_creds():
            print('Given credentials are invalid!')
            os.remove(r'C:\Teams Bot\login.txt')
            print('RESTART PROGRAM TO PASS THE CREDENTIALS AGAIN')
            # Remove login.txt and ask about email and password again

        bot = Bot(EMAIL, PASSWORD, incorrect_creds=incorrect_creds)
        bot.start()
