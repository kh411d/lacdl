# [generic] 37: Downloading m3u8 information
# [info] Available formats for 37:
# format code  extension  resolution note
# 400          mp4        640x360     400k
# 800          mp4        854x480     800k
# 1300         mp4        1280x720   1300k
# 2000         mp4        1920x1080  2000k  (best)

from __future__ import unicode_literals
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import sys, time, argparse
import youtube_dl
import os
import re
import json
import html2markdown
import glob

parser=argparse.ArgumentParser()

parser.add_argument('--uname', help='Username')
parser.add_argument('--pwd', help='password')
parser.add_argument('--url', help='parent url')
parser.add_argument('--cookie', help='use existing cookie True/False', type= bool, default=False)
parser.add_argument('--skip', help='skip number', type= int, default= 0)

args=parser.parse_args()

username = args.uname
pwd = args.pwd
url = args.url
useOldCookie = args.cookie
skip = args.skip
  

cookie_file = 'cookies.txt'
cookie_json = 'cookies.json'

# remove cookie file if it exists
if not useOldCookie and os.path.exists( cookie_file ):
   os.remove( cookie_file )
if not useOldCookie and os.path.exists( cookie_json ):
   os.remove( cookie_json )

# recreate file and open in append mode
mode = 'r' if useOldCookie else 'a+'
f = open(cookie_file, mode)
fc = open(cookie_json, mode)


# cookie function
def get_cookies():
  expiry = 0
  if useOldCookie:
    ffc = fc.readlines()
    for x in ffc:
      driver.add_cookie(json.loads(x)) 
  else:
    for i in driver.get_cookies():
      if not i.get('expiry'):
          expiry = 0
      else:
          expiry = i.get('expiry')
      cookie = '{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format( i['domain'], str( i['httpOnly'] ).upper(), i['path'], str( i['secure'] ).upper(), expiry, i['name'], i['value'] )
      fc.write(json.dumps(i) + '\n')
      f.write( cookie )

# chrome options
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")

# initiate browser 
driver = webdriver.Chrome( options=options )

driver.implicitly_wait(5)
wait = WebDriverWait(driver, 5)

# navigate to Linux Academy
print("Opening https://linuxacademy.com/")
driver.get("https://linuxacademy.com/")


if not useOldCookie:
  # click login link
  link = driver.find_element_by_partial_link_text('Log In')
  link.click()

  # get cookies from login.linuxacademy.com
  print("Getting cookies from login.linuxacademy.com")
  get_cookies()

  # wait until login screen appears 
  print("Sleeping for 5 seconds..")
  time.sleep(5)

  print("Attempting to login..")
  user = driver.find_element_by_name('username')
  user.send_keys( username )
  password = driver.find_element_by_name('password')
  password.send_keys( pwd )
  password.send_keys(Keys.RETURN)

  # check login
  time.sleep(30)
  try:
      lname = driver.find_element_by_id('navigationUsername')
      if lname:
        print("Login successful..")
  except:
      print("Login failed..exiting")
      exit()

# get cookies from .linuxacademy.com
print('Getting cookies from .linuxacademy.com')
get_cookies()

# get lesson links 
print("Getting lesson links..")
driver.get( url )
time.sleep(5)
lessons = driver.find_elements_by_tag_name('a')
urls = []
excs = []

for i in lessons:
    try:
       lesson  =  i.get_attribute('href')
       if '/course/' in lesson:
          urls.append( lesson )
       elif '/exercises/' in lesson:
          excs.append(lesson)
    except:
      print('ignoring URL')
      #print(sys.exc_info())

#skip by number
urls = urls[skip:]

#Get video description
print('Get video description')
counter = skip
for u in urls:
  counter = counter + 1
  driver.get(u)
  wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".video-details-row")))
  title = driver.find_element_by_css_selector('div.video-header-trail-inner:nth-child(1) > h2:nth-child(1)').text
  cx = driver.find_element_by_css_selector('.video-details-row > div:nth-child(1) > div:nth-child(1)').get_attribute('innerHTML')
  fname = str('%05d' % counter) + "-" + re.sub(r'Lecture|\W+', '', title) + ".md"
  fd = open(  fname , 'w+')
  print(fname)
  mdtext = html2markdown.convert(cx)
  fd.write(mdtext.encode('ascii', 'ignore').decode('ascii'))
  fd.close()

#Get Exercises
if len(excs) > 0: 
  print('Get Exercises')
  ecnt = 0
  for e in excs:
    ecnt = ecnt + 1
    driver.get(e)
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".exercise-title")))
    excTitle = driver.find_element_by_css_selector('.exercise-title').text
    efname = str(ecnt) + "-" + re.sub(r'\W+', '', excTitle) + ".md"
    efd = open(  efname , 'w+')
    print(efname)
    eInstruction = html2markdown.convert(driver.find_element_by_css_selector('.instructions-container').text)
    driver.execute_script("document.getElementsByClassName('solutions-container')[0].style.display = 'block'")
    WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".solutions-container")))
    eSolution = html2markdown.convert(driver.find_element_by_css_selector('.solutions-container').text)
    efd.write("***INSTRUCTION***\n\n")
    efd.write(eInstruction.encode('ascii', 'ignore').decode('ascii'))
    efd.write("\n\n\n\n")
    efd.write("***SOLUTION***\n\n")
    efd.write(eSolution.encode('ascii', 'ignore').decode('ascii'))
    efd.close()

    

# close file handle
f.close()
fc.close()

# convert cookie using curl
print("Converting cookie using curl..")
cleaned_file = 'curlcookies.txt'
os.system('curl -b {} --cookie-jar {} {}'.format( cookie_file, cleaned_file, url  ) )

# call youtube-dl
print("Starting download..")

ydl_opts = { 'cookiefile': cleaned_file, 'force_generic_extractor': True , 'outtmpl':   '%(autonumber)s-%(id)s-%(title)s.%(ext)s', 'restrictfilenames': True , 'sleep_interval': 20, 'format':'800' }

with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download( urls  )


# rename files
print("Renaming files")
mp4s = glob.glob('*.mp4')
mds = glob.glob('*.md')
mp4s.sort()
mds.sort()

k = skip
for idx in range(len(mds)):
  k = k + 1 
  nn = re.sub(r'^[0-9]+', str(k), mds[idx])
  os.rename(mds[idx], nn)
  os.rename(mp4s[idx],nn[0:(len(nn)-3)] + ".mp4")

# quit
print("ALL DONE")


driver.quit()
