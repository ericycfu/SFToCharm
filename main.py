import asyncio

import requests
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import (charm_password, charm_username, client_id, client_secret,
                    password, username)
from salesforce.models import SFTempAccount, SFTempContact, CharmPatient
from salesforce.salesforce_api import SalesForceSession

driver = None

def main():
    loop = asyncio.get_event_loop()
    charm_members = loop.run_until_complete(get_charm_patients())
    print('done grabbing member info')
    
    #navigate to page to add patients
    global driver
    driver = webdriver.Firefox()
    login()
    navigate_to_patients()

    #do one to test it
    charm_members = charm_members[0:1]
    for member in charm_members:
        add_member(member)

    log_out()

#TODO: Validate information, 
async def get_charm_patients():
    sf_lib = SalesForceSession(client_id, client_secret, username, password)
    await sf_lib.get_token()

    print('getting tempaccounts')
    tempaccounts = await sf_lib.get_all_objects_of_type(SFTempAccount)

    print('getting tempcontacts')
    tempcontacts = await sf_lib.get_all_objects_of_type(SFTempContact)
    tempcontacts = [x for x in tempcontacts if x.TempAccount__c]

    member_account_contact_pairs = []
    #pair the tempaccount with main tempcontact
    for tempaccount in tempaccounts:
        try:
            related_tcs = [tc for tc in tempcontacts if tc.TempAccount__c == tempaccount.Id]
            #get primary tc. Person with same firstname, lastname and then oldest person if two people have same name
            name_arr = tempaccount.Name__c.split(",")
            name_arr = [x.lower().strip() for x in name_arr]
            first_name = name_arr[1]
            last_name = name_arr[0]
            same_name_tcs = [tc for tc in related_tcs if tc.FirstName__c.lower() == first_name if tc.LastName__c.lower() == last_name]
            #since all dates have same format: yyyy-mm-dd, taking min will get oldest one
            tc = min(same_name_tcs, key = lambda x : x.BirthDate__c)
            member_account_contact_pairs.append((tempaccount, tc))
        except Exception as e:
            print(f'Something wrong with tempaccount: {tempaccount}')
            raise e

    charm_members = []
    for ta, tc in member_account_contact_pairs:
        charm_members.append(CharmPatient(tc.FirstName__c, tc.LastName__c, tc.BirthDate__c, tc.Gender__c, ta.Phone__c, ta.Primary_Email__c))
    print(f"number new accounts: {len(charm_members)}")

    await sf_lib.close_session()
    charm_members.insert(0, CharmPatient('Eric','Fu', '06-11-1998', 'Male', '4403192041', 'eric.fu@bowtiemedical.com'))
    return charm_members


def login():
    driver.get('https://ehr2.charmtracker.com/')

    email = driver.find_element_by_id('login_id')
    email.send_keys(charm_username)
    
    next_button = driver.find_element_by_id('nextbtn')
    next_button.click()

    password = driver.find_element_by_id('password')
    password.send_keys(charm_password)

    #sometimes it is too fast and doesn't click the next_button. Since they reuse the same button.
    WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.ID, 'nextbtn')))
    next_button.click()

def navigate_to_patients():
    #sometimes it lags and takes a long time
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'BowTie Medical')))
    bowtie_link = driver.find_element_by_partial_link_text('BowTie Medical')
    bowtie_link.click()

    #at the current time, this is a div belonging to the patients icon.
    patients_icon = driver.find_element_by_id('MEMBER_TAB_ID_1')
    patients_icon.click()

def add_member(member):

    add_patients_button = driver.find_element_by_xpath('//div[text() = \'Patient\']')
    add_patients_button.click()

    first_name = driver.find_element_by_id('patient_first_name')
    first_name.send_keys(member.first_name)

    last_name = driver.find_element_by_id('patient_last_name')
    last_name.send_keys(member.last_name)

    dob = driver.find_element_by_id('patient_dob')
    dob.send_keys(member.dob)

    gender_select = driver.find_element_by_id('patient_gender')
    gender_select.click()
    gender_option = driver.find_element_by_xpath(f'//option[contains(text(), \'{member.gender}\')]')
    gender_option.click()
    driver.execute_script(f"document.getElementById('patient_mobile').value='{member.phone}'")

    email = driver.find_element_by_id('patient_email')
    email.send_keys(member.email)

    #submit = driver.find_element_by_xpath('//button[contains(text(), \'Add\')]')
    #submit.click()


    
def log_out():
    profile_pic = driver.find_element_by_id("accMemberPhoto")
    profile_pic.click()

    sign_out_button = driver.find_element_by_xpath('//button[contains(text(), \'Sign Out\')]')
    driver.execute_script("arguments[0].click()", sign_out_button) #normal way doesn't work, even with web driver wait


    







if __name__ == '__main__':
    main()
