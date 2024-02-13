from selenium import webdriver
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import random
from bs4 import BeautifulSoup
import requests
from pathlib import Path
import sys
import json

# for v3, check all the links in array and get categories for each using bs4


# returns to the home screen after ever watched video as opposed to selecting from side bar
# expected results: less errors and crashes due to inconsistent side bar recommendation formats

# user setable variables
hour_block = 3 # time of a simulation partition in seconds
maximum_watch_time = 180 # 3 minutes in seconds
days_to_run = 30
df_cred = pd.read_csv('credentials.csv')
password = df_cred['password'][1]
email = df_cred['email'][1]

# fixed variables
hours_in_day = 24
sim_partition_time = hour_block * 60 * 60 # 6 hours in seconds

# for testing
sim_partition_time = 100
# for testing
maximum_watch_time = 5
def create_json(link):
    listed = requests.get(link)
    soup = BeautifulSoup(listed.text, "html.parser")
    duration = soup.find(itemprop='duration')['content'][2:-1]
    dur_part = duration.partition('M')
    duration = int(int(dur_part[0]) * 60 + int(dur_part[2]))
    tags = soup.find_all(property='og:video:tag')
    tags = [item['content'] for item in tags]

    vid = {
        "url":link,
        "title":soup.find('title').text,
        "tags":tags,
        "views":soup.find(itemprop='interactionCount')['content'],
        "duration":duration,
        "category":soup.find(itemprop='genre')['content']
    }
    return vid

def run_data_collection(sim_partition_time, email, password):
    # attempts to login to google account
    try:
        driver = webdriver.Firefox()
        driver.get('https://www.youtube.com/')
        login_page = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                                    (By.XPATH,'//*[@id="buttons"]/ytd-button-renderer/yt-button-shape/a')))
        login_page.click()
        time.sleep(1)
        driver.find_element(By.XPATH,'//*[@id ="identifierId"]').send_keys(email)
        driver.find_element(By.XPATH,'//*[@id ="identifierNext"]').click()
        pword_entry = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                                    (By.XPATH,'//*[@id="password"]/div[1]/div/div[1]/input')))
        pword_entry.send_keys(password)
        time.sleep(1)
        driver.find_element(By.XPATH,'//*[@id ="passwordNext"]').click()
    except:
        # failed to login, restart program and try again
        print("failed to login, restarting program")
        run_data_collection(sim_partition_time, email, password)
    
    for day in range(1,days_to_run + 1):
        for hour_itter in range(0,int(hours_in_day / hour_block)):
            #df_watched = pd.DataFrame(columns=['title','url','time watched','category'])
            watched_list = {}
            col_labels = ["video #" + str(i) for i in range(1,21)]
            vid_list = {}
            rec_count = 0
            watch_count = 0
            # gives 5 seconds for webpage to load
            time.sleep(5)
            # starts collecting data for a single partition 0-3hr block of time
            try:
                start_time = time.time()
                # runs the program for the simulation time
                while (time.time() - start_time) < sim_partition_time:
                    # initialize list for recommended videos (20 videos per loop)
                    rec_label = "Set " + str(rec_count)
                    vid_list[rec_label] = {}
                    video_page = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="logo"]')))
                    video_page.click()
                    time.sleep(5)
                    # gathers all videos on home page into array for titles and links
                    home_page = driver.find_elements(By.XPATH,'//*[@id="video-title-link"]')
                    links = []
                    for elem in home_page:
                        links.append(elem.get_attribute('href'))
                        
                    # randomly selects one video (only picks from up to first 20 videos)
                    vid_index = random.randint(0,min(len(links) - 1, 19))
                    # normalizes recommendation length
                    while len(links) < 20:
                        links.append('')

                    # visit selected video
                    driver.get(links[vid_index])

                    # skip ad if ad is playing #################

                    # play the video
                    play_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                                            (By.ID, 'movie_player')))
                    play_button.send_keys(Keys.SPACE)
                    # start the timer
                    time_remaining = (sim_partition_time - (time.time() - start_time))                    
                    # get json file of watched video
                    watched_json = create_json(links[vid_index])
                    duration = watched_json["duration"]
                    # create json of other recommened videos              
                    for i, link in enumerate(links[:20]):
                        if link != '':
                            vid_list[rec_label][i] = create_json(link)
                    rec_count += 1
                    # if duration exceeds timer, end early      
                    if 0 > time_remaining:
                        duration = 0
                    elif time_remaining < maximum_watch_time:
                        duration = abs(time_remaining)
                    elif duration > maximum_watch_time:
                        duration = maximum_watch_time

                    # add new video
                    #df_watched.loc[len(df_watched)] = [titles[vid_index],links[vid_index],duration,category]
                    watched_list[watch_count] = watched_json
                    watch_count += 1
                    
                    # wait until video done playing
                    # time.sleep(duration)
                    time.sleep(5)
            except Exception as e:
                print(str(e) + " Error has occured")
                driver.quit()
                sys.exit()
            finally:
                filepath = Path('data/day_'+str(day)+'/'+'day'+str(day)+'_recommended_'
                                +str((hour_block*hour_itter))+'_'
                                +str((hour_block*hour_itter+hour_block))+'hr.json')  
                filepath.parent.mkdir(parents=True, exist_ok=True)
                json_file = json.dumps(vid_list, indent=4)
                with open(filepath, "w") as out:
                    out.write(json_file)
                #df_recommended.to_csv(filepath)

                filepath = Path('data/day_'+str(day)+'/'+'day'+str(day)+'_watched_'
                                +str((hour_block*hour_itter))+'_'
                                +str((hour_block*hour_itter+hour_block))+'hr.json')  
                filepath.parent.mkdir(parents=True, exist_ok=True)
                #df_watched.to_csv(filepath)
                json_file = json.dumps(watched_list, indent=4)
                with open(filepath, "w") as out:
                    out.write(json_file)
    # exit application after finishing all daily data collection
    driver.quit()

run_data_collection(sim_partition_time, email, password)