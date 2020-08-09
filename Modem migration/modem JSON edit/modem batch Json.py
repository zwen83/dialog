# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author: zwen time:2020/7/22


#!/usr/bin/env python

# This script is essentially meant for Orbith to modify the flash config file of MDM2210 using the modem JSON API
# Parameters that need to be added are: "rxedit=expert", "oduedit=expert", "antedit=expert"

__author__ = "mabu@newtec.eu"

import re
import csv
import datetime
import time
import logging


# sending http request to the modem based on the passed function (GetDeviceInformation, GetFlashConfig, etc..)
def sendRequest(func, method):
    import requests
    global status
    try:
        time.sleep(5)

        if run_from_hub:
            # In case the script will be running from the hub .. no mgmt IP is needed, only the remoteGuiUrl
            url = "http://localhost" + remoteGuiUrl + "cgi-bin/cgiclient"
        else:
            # In case the script will be running from a laptop connected directly to the modem
            url = 'http://' + mgmtIP + '/cgi-bin/cgiclient'

        if method == "GET":
            url = url + '?request='
            res = requests.get(url + func, timeout=5)
            res_data = res.json()
            return res_data

        elif method == "POST":
            headers = {'TextId': 'request'}
            res = requests.post(url, data=func, headers=headers, timeout=5)
            stringRes = str(res)
            logger.debug("POST Response: " + stringRes)
            if stringRes.find("200") != -1:
                logger.info("Setting status to Success.")
                status = "Success"
            return res

        else:
            logger.debug("unknown method .. method should be POST or GET !!")
            return "NA"

    except requests.exceptions.RequestException as e:
        logger.error("sendRequest(): requests.exceptions.RequestException!")
        raise e
    except Exception as e:
        logger.error("sendRequest(): error while sending a request to the modem.")
        raise e


# getting the sw version of a modem
def getSwVersion():
    func = '{"FunctionName":"GetDeviceInformation"}'
    method = "GET"
    try:
        resData = sendRequest(func, method)
        swVersion = resData['RequestData']['Software']['CurrentVersion']
        logger.debug('SW Version: ' + swVersion)
        return swVersion
    except Exception as e:
        logger.error("getSwVersion(): error getting the SW version.")
        raise e


# authenticating and returning the sessionID
def authenticate(adminPwd):
    func = '{"FunctionName":"AuthenticatePassword","Params":{"LoginLevel":"admin","Password":"' + adminPwd + '"}}'
    method = "GET"
    resData = sendRequest(func, method)
    try:
        sessionID = resData['RequestData']['SessionId']
        logger.debug("session ID: " + sessionID)
        return sessionID
    except (ValueError, TypeError) as e:
        logger.error("authenticate(): please check admin password!")
        raise e
    except Exception as e:
        logger.error("authenticate(): error authenticating the modem.")
        raise e


# getting flash config
def getFlashCfg(sessionID):
    func = '{"FunctionName":"GetFlashConfig","SessionId":"' + sessionID + '"}'
    method = "GET"
    try:
        resData = sendRequest(func, method)
        flashCfg = resData['RequestData']['FlashConfig']
        return flashCfg
    except Exception as e:
        logger.error("getFalshCfg(): error getting the flashCfg of the modem.")
        raise e


def rebootModem():
    logger.info("Modem will be rebooted!")
    func = '{"FunctionName":"Reboot"}'
    method = "GET"
    try:
        sendRequest(func, method)
    except Exception as e:
        logger.error("rebootModem(): error rebooting the modem.")
        raise e


# Adding parameters to flash config, and changing expert user password
def modifyFlashCfg(adminPwd, oldNtciPwd, newNtciPwd, oldFacNtciPwd, newFacNtciPwd):
    rxedit = "rxedit"
    oduedit = "oduedit"
    antedit = "antedit"
    param = [rxedit, oduedit, antedit]
    ntci = "ntcipasswd"
    fac_ntci = "fac_ntcipasswd"

    sessionID = authenticate(adminPwd)
    flashCfg = getFlashCfg(sessionID)

    # stripping in case of white spaces or new line
    newFlashCfg = flashCfg.rstrip()

    # searching for patter ntcipasswd=s3p and replace it if found
    match = re.search(r"(^|\n)%s=%s($|\n)" % (ntci, oldNtciPwd), newFlashCfg)
    if match:
        newFlashCfg = re.sub(r"(^|\n)%s=%s($|\n)" % (ntci, oldNtciPwd),
                             r"\1%s=%s\2" % (ntci, newNtciPwd),
                             newFlashCfg)
        logger.info("ntcipasswd has been changed to: " + newNtciPwd)
    else:
        # if old password is different than s3p .. then we don't change it
        logging.error("ntcipasswd old password is not the default no changes will be done.")

    # searching for patter fac_ntcipasswd=s3p and replace it if found
    match = re.search(r"(^|\n)%s=%s($|\n)" % (fac_ntci, oldFacNtciPwd), newFlashCfg)
    if match:
        newFlashCfg = re.sub(r"(^|\n)%s=%s($|\n)" % (fac_ntci, oldFacNtciPwd),
                             r"\1%s=%s\2" % (fac_ntci, newFacNtciPwd),
                             newFlashCfg)
        logger.info("fac_ntcipasswd has been changed to: " + newFacNtciPwd)
    else:
        # if old password is different than s3p .. then we don't change it
        logging.error("fac_ntcipasswd old password is not the default no changes will be done.")

    # adding parameters; replacing the lines if it already exists
    i = 0
    for i in range(len(param)):
        match = re.search(r"(^|\n)%s=%s($|\n)" % (param[i], r"\w*"), newFlashCfg)
        if match:
            logger.info(param[i] + "=expert already exists in flashCfg but it will be updated anyway.")
            newFlashCfg = re.sub(r"(^|\n)%s=%s($|\n)" % (param[i], r"\w*"),
                                 r"\1%s=%s\2" % (param[i], "expert"),
                                 newFlashCfg)
            i += 1
        else:
            logger.error(param[i] + "=expert will be added to flashCfg.")
            newFlashCfg = newFlashCfg + "\n" + param[i] + "=expert"
            i += 1

    # searching for \ or "
    match = re.search(r"[\\\"]", newFlashCfg)

    # escaping special characters \ and "
    if match:
        newFlashCfg = re.sub(r'([\\\"])', r"\\\1", newFlashCfg)

    newFlashCfg = newFlashCfg.rstrip()  # stripping in case of white spaces or new line at the end of file

    # sending the new flash config
    if newFlashCfg is not None:
        func = {
            'request': '{"SessionId": "' + sessionID +
                       '", "FunctionName":"SetFlashConfig","Params": {"FlashConfig":"' + newFlashCfg + '"}}'}
        method = "POST"
        return sendRequest(func, method)
    else:
        logger.error("New flash config has not been sent !!")


# getting mgmt IP address from CMS
def getRemoteURL(macAddress):
    import requests
    url = "http://localhost/rest/modem/collect?property=satelliteNetworkConfigurations&macAddress=" + macAddress
    logger.info(url)
    headers = {
        'authorization': "Basic aG5vOkQhQDEwZw==",
        'cache-control': "no-cache",
    }
    try:
        time.sleep(5)
        response = requests.request("GET", url, headers=headers)
        json_data = response.json()
        # mgmtIP = json_data[0]["satelliteNetworkConfigurations"][0]["managementAddress"]
        # remoteGuiUrl = json_data[0]["satelliteNetworkConfigurations"][0]["remoteGuiUrl"]
        return json_data[0]["satelliteNetworkConfigurations"][0]["remoteGuiUrl"]
    except Exception as e:
        logger.error("getRemoteURL(): error getting the remote URL of the modem")
        raise e


# writing to result.csv
def writeToCsv(terminalsList, counter, macAddress, adminPwd, terminalSW, oldNtciPwd, newNtciPwd, oldFacNtciPwd, newFacNtciPwd):
    terminal_list = []
    try:
        # Read all data from the csv file.
        with open(terminalsList, 'rb') as b:
            lines = csv.reader(b)
            terminal_list.extend(lines)

        now = datetime.datetime.now()

        line_to_override = {counter: [macAddress, adminPwd, oldNtciPwd, newNtciPwd, oldFacNtciPwd, newFacNtciPwd,
                                      status, terminalSW, now.strftime("%Y-%m-%d %H:%M")]}
        logger.debug("New row: ")
        logger.debug(line_to_override)
        logger.debug("\n")
        # Write data to the csv file and replace the lines in the line_to_override dict.
        with open(terminalsList, 'wb') as b:
            writer = csv.writer(b)
            for line, row in enumerate(terminal_list):
                data = line_to_override.get(line, row)
                writer.writerow(data)
    except Exception as e:
        logger.error("writeToCsv(): error writing to CSV file.")
        raise e


# global variables
run_from_hub = False
status = "Failed"
mgmtIP = "NA"
remoteGuiUrl = "NA"
logger = None


def main():
    import ConfigParser

    global logger
    global run_from_hub
    global remoteGuiUrl
    global mgmtIP
    global status

    oldNtciPwd = "NA"
    newNtciPwd = "NA"
    oldFacNtciPwd = "NA"
    newFacNtciPwd = "NA"

    macAddress = "NA"
    terminalSW = "NA"
    successfulTerminals = 0
    failedTerminals = 0
    counter = 0

    config = ConfigParser.ConfigParser()
    config.readfp(open('config.ini'))

    # getting values from config.ini
    script_mode = config.get("script", "mode")
    terminalsList = config.get("script", "terminalsList")

    logFile = config.get("logging", "logFile")
    sleepingTime = config.getint("generic", "sleepingTime")

    if script_mode == "hub":
        run_from_hub = True
        # num_of_modems = config.getint("hub", "num_of_modems")
    else:
        # num_of_modems = 1
        mgmtIP = config.get("local", "modemIp")

    # the time the script will stop at .. in case it is running in a maintenance window
    maintenance_window = config.getboolean("hub", "maintenance_window")
    end_hour = config.getint("hub", "end_hour")
    end_min = config.getint("hub", "end_min")
    end_time = end_hour * 60 + end_min

    pattern = re.compile("^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")

    logger = logging.getLogger("gui_protector")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    handler = logging.FileHandler(logFile)
    streamHandler = logging.StreamHandler()

    handler.setFormatter(formatter)
    streamHandler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    streamHandler.setLevel(logging.INFO)

    logger.addHandler(handler)
    logger.addHandler(streamHandler)

    logger.info("****************************Start of script****************************")

    logger.info("logging to: " + logFile)
    logger.info("reading from: " + terminalsList)

    with open(terminalsList) as csvFile:
        reader = csv.reader(csvFile, delimiter=',')
        next(reader, None)
        for row in reader:
            # Stop the script at specific hour
            if maintenance_window:
                current_hour = datetime.datetime.now().hour
                current_min = datetime.datetime.now().minute
                current_time = current_hour * 60 + current_min
                if current_time > end_time:
                    logger.info("Maintenance windows time is over. The script will stop!")
                    break
            counter += 1
            logger.info("***************************** Terminal #" + str(counter) + " *****************************")
            logger.debug("Original row: ")
            logger.debug(row)
            try:
                macAddress = row[0]
                adminPwd = row[1]
                oldNtciPwd = row[2]
                newNtciPwd = row[3]
                oldFacNtciPwd = row[4]
                newFacNtciPwd = row[5]
                status = row[6]
            except Exception as error:
                logger.error("Exception while reading values from csv file: ")
                logger.error(error)

            logger.info("Terminal: " + macAddress + " original status: " + status)

            if status == "Success":
                logger.info("Terminal has been already processed.")
            else:
                # in case of an empty line (at the end of the file)
                # or NA/wrong value of a mac address; reading from csv file should stop
                if pattern.match(macAddress.rstrip()):
                    logger.info("Terminal will be processed.")
                    try:
                        if run_from_hub:
                            remoteGuiUrl =getRemoteURL(macAddress)
                            if remoteGuiUrl == "NA":
                                logger.info(macAddress + " -> Script will process the next modem.")
                                time.sleep(sleepingTime)
                                continue
                        terminalSW = str(getSwVersion())
                        modifyFlashCfg(adminPwd, oldNtciPwd, newNtciPwd, oldFacNtciPwd, newFacNtciPwd)
                        rebootModem()
                        writeToCsv(terminalsList, counter, macAddress, adminPwd, terminalSW, oldNtciPwd,
                                   newNtciPwd, oldFacNtciPwd, newFacNtciPwd)
                        logger.info("Terminal with MAC address " + macAddress + " has been processed with status: "
                                    + status)
                        if status == "Success":
                            successfulTerminals += 1
                        else:
                            failedTerminals += 1

                        logger.info("Number of successful terminals = " + str(successfulTerminals))
                        logger.info("Number of failed terminals = " + str(failedTerminals))
                        logger.info("Script will wait for " + str(sleepingTime) +
                                    " sec before processing the next terminal.")
                        time.sleep(sleepingTime)

                    except Exception as error:
                        logger.error("Exception at main: ")
                        logger.error(error)
                        status = "Failed"
                        writeToCsv(terminalsList, counter, macAddress, adminPwd, terminalSW, oldNtciPwd,
                                   newNtciPwd, oldFacNtciPwd, newFacNtciPwd)
                        logger.info("Terminal with MAC address " + macAddress + " has been processed with status: "
                                    + status)
                        failedTerminals += 1
                        logger.info("Number of successful terminals = " + str(successfulTerminals))
                        logger.info("Number of failed terminals = " + str(failedTerminals))
                        logger.info("Script will wait for  " + str(sleepingTime) +
                                    " seconds before processing the next terminal.")
                        time.sleep(sleepingTime)
                else:
                    logger.debug("Invalid MAC address --> " + macAddress)
                    break
        logger.info("***********************************************************************")
        logger.info("No more Terminals to be processed.")
    logger.info("****************************End of script******************************")
    return True


if __name__ == "__main__":
    main()