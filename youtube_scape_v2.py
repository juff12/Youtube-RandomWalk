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

# for v3, check all the links in array and get categories for each using bs4


# returns to the home screen after ever watched video as opposed to selecting from side bar
# expected results: less errors and crashes due to inconsistent side bar recommendation formats

# user setable variables
hour_block = 3 # time of a simulation partition in seconds
maximum_watch_time = 180 # 3 minutes in seconds
days_to_run = 30
df_cred = pd.read_csv('YoutubeCrawler/credentials.csv')
password = df_cred['password'][0]
email = df_cred['email'][0]

# fixed variables
hours_in_day = 24
sim_partition_time = hour_block * 60 * 60 # 6 hours in seconds

# for testing
sim_partition_time = 30


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
            df_watched = pd.DataFrame(columns=['title','url','time watched','category'])
            col_labels = ["video #" + str(i) for i in range(1,21)]
            df_recommended = pd.DataFrame(columns=col_labels)
            # gives 5 seconds for webpage to load
            time.sleep(5)
            # starts collecting data for a single partition 0-3hr block of time
            try:
                start_time = time.time()
                # runs the program for the simulation time
                while (time.time() - start_time) < sim_partition_time:
                    video_page = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                                            (By.XPATH,'//*[@id="logo"]')))
                    video_page.click()
                    time.sleep(5)
                    # gathers all videos on home page into array for titles and links
                    home_page = driver.find_elements(By.XPATH,'//*[@id="video-title-link"]')
                    links, titles = [], []
                    for elem in home_page:
                        links.append(elem.get_attribute('href'))
                        titles.append(elem.get_attribute('title'))
            
                    # randomly selects one video (only picks from up to first 20 videos)
                    vid_index = random.randint(0,min(len(titles) - 1, 19))
                    # normalizes recommendation length
                    while len(titles) < 20:
                        titles.append('')
                    df_recommended.loc[len(df_recommended)] = titles[:20] # add first 20 video recommendations
                    
                    # visit selected video
                    driver.get(links[vid_index])

                    # skip ad if ad is playing
                    #
                    #

                    # play the video
                    play_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                                            (By.ID, 'movie_player')))
                    play_button.send_keys(Keys.SPACE)
                    # get duration of video
                    listed = requests.get(links[vid_index])
                    soup = BeautifulSoup(listed.text, "html.parser")
                    category = soup.find(itemprop='genre')['content']
                    duration = soup.find(itemprop='duration')['content'][2:-1]
                    dur_part = duration.partition('M')
                    duration = int(int(dur_part[0]) * 60 + int(dur_part[2]))
                    
                    # if duration exceeds timer, end early      
                    time_remaining = (sim_partition_time - (time.time() - start_time))
                    if 0 > time_remaining:
                        duration = 0
                    elif time_remaining < maximum_watch_time:
                        duration = abs(time_remaining)
                    elif duration > maximum_watch_time:
                        duration = maximum_watch_time

                    # add new video
                    df_watched.loc[len(df_watched)] = [titles[vid_index],links[vid_index],duration,category]
                    
                    # wait until video done playing
                    # time.sleep(duration)
                    time.sleep(5)
            except Exception as e:
                print(e)
                driver.quit()
                sys.exit()
            finally:
                filepath = Path('YoutubeCrawler/data/day_'+str(day)+'/'+'day'+str(day)+'_recommended_'
                                +str((hour_block*hour_itter))+'_'
                                +str((hour_block*hour_itter+hour_block))+'hr.csv')  
                filepath.parent.mkdir(parents=True, exist_ok=True)
                df_recommended.to_csv(filepath)
                filepath = Path('YoutubeCrawler/data/day_'+str(day)+'/'+'day'+str(day)+'_watched_'
                                +str((hour_block*hour_itter))+'_'
                                +str((hour_block*hour_itter+hour_block))+'hr.csv')  
                filepath.parent.mkdir(parents=True, exist_ok=True)
                df_watched.to_csv(filepath)
    
    # exit application after finishing all daily data collection
    driver.quit()

run_data_collection(sim_partition_time, email, password)