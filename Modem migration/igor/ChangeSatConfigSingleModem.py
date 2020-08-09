__author__ = 'isim'
__version__ = 2.0

import json
from time import sleep
import rest as REST 

import logging
logger = logging.getLogger('SingleModem')
logger.setLevel(logging.INFO)

#--------------------------------------------------------------------------#
#------ Procedure that sends a JSON request to a modem --------------------#
#--------------------------------------------------------------------------#
def _SendJSONRequest(rest, url, functionName, params = ''):
    result = False
    urlParams = {'request':'{"FunctionName":"%s"%s}' % (functionName, (', "Params": %s' % json.dumps(params)  if params else ''))}
    logger.debug('Sending %s %s', functionName, ('with Params: %s' % params if params else ''))
    try:
        reply = rest.GET('cgi-bin/cgiclient', '', url, params=urlParams)
    except REST.ConnectionError:
        logger.critical('Network connection error')
        exit(1)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    logger.debug('Received reply: %s', reply)
    try:
        if reply['RequestResult']['Success']:
            if 'RequestData' in reply:
                result = reply['RequestData']
            else:
                result = True
    except KeyError:
        logger.debug('Reply is corrupted')
        result = False
    except TypeError:
        result = False
    return result


#--------------------------------------------------------------------------#
#------ Procedure that really does the job --------------------------------#
#--------------------------------------------------------------------------#
def ProcessSingleModem(rest, url, airmac, mainCarrier, altCarrier, odu=False, checkAfterChange=False, reboot=True, pauseAfterChange=False, pauseAfterReboot=False):
    result = (airmac, '')
    try:
        reply = _SendJSONRequest(rest, url, 'GetAirMACAddress')
        airMACAddress = reply['AirMACAddress']
        if airmac:
            if airmac.lower() != airMACAddress.lower():
                logger.warning('AirMACAddress expeted ' + airmac + ' but the remote modem replied with ' + airMACAddress)
                return False
        else: airmac = airMACAddress
        
        if odu:
            reply = _SendJSONRequest(rest, url, 'GetODUTypes')
            oduTypes = reply['ODUTypes']
            bExisting = False
            ODUTypeId = odu.pop('ODUTypeId')
            Description = odu.pop('Description')
            if oduTypes and type(oduTypes) == list and len(oduTypes) > 0:
                for oduType in oduTypes:
                    if oduType['Id'] == 'ODUTypeId':
                        bExisting = True
                        break
            if bExisting:
                currentODU = _SendJSONRequest(rest, url, 'GetODUTypeData', {'ODUTypeId': ODUTypeId})
                for value in ['LO', 'RFStart', 'RFStop']:
                    if odu['LowBand'][value] == '':
                        odu['LowBand'][value] = currentODU['LowBand'][value]
                for key in odu.keys():
                    if odu[key] == '':
                        odu[key] = currentODU[key]
                if odu['TransmitterType'] == 'buc':
                    odu.pop('MUCData')
                    for value in ['LO', 'RFStart', 'RFStop']:
                        if odu['BUCData'][value] == '':
                            odu['BUCData'][value] = currentODU['BUCData'][value]
                else:
                    odu.pop('BUCData')
                    for value in ['Multiplicator', 'RFStart', 'RFStop']:
                        if odu['MUCData'][value] == '':
                            odu['MUCData'][value] = currentODU['MUCData'][value]
                reply = _SendJSONRequest(rest, url, 'SetODUTypeData', {'ODUTypeId': ODUTypeId, 'ODUTypeData': odu})
            else:
                if odu['TransmitterType'] == '':
                    logger.error('For new ODUs either "bucMultiplicator" or "bucLO" should be defined')
                    return False
                if odu['TransmitterType'] == 'buc':
                    odu.pop('MUCData')
                else:
                    odu.pop('BUCData')
                for value in ['LO', 'RFStart', 'RFStop']:
                    if odu['LowBand'][value] == '':
                        odu['LowBand'][value] = 0
                    if odu['HighBand'][value] == '':
                        odu['HighBand'][value] = 0
                for key in ['LnbTXMin', 'LnbTXMax', 'LnbRXMin', 'LnbRXMax', 'TXDetectionFreq', 'PoweroffTimeout', 'ElevationOffset', 'FeedReadingWhenRxHor', 'LinearPolarizationIndication', 'PolarizationStackingOffset']:
                    if odu[key] == '':
                        odu[key] = 0
                for key in ['TxDetectionAvailable', 'TxDcOutput', 'Buc10MhzOutput', 'BucModemSynced']:
                    if odu[key] == '':
                        odu[key] = False
                if odu['PositiveFeedReading'] == '':
                    odu['PositiveFeedReading'] = 'clockwise'
                if odu['ReflectorType'] == '':
                    odu['ReflectorType'] = 'single-offset'
                if odu['ToneSelection'] == '':
                    odu['ToneSelection'] = 'off'
                if odu['VoltageSelection'] == '':
                    odu['VoltageSelection'] = 'off'
                reply = _SendJSONRequest(rest, url, 'AddODUType', {'ODUTypeId': ODUTypeId, 'ODUTypeData': odu, 'Description': Description})

        reply = _SendJSONRequest(rest, url, 'GetActiveODUType')
        activeODUTypeId = reply['ODUTypeId']
        activeODU = _SendJSONRequest(rest, url, 'GetODUTypeData', {'ODUTypeId': activeODUTypeId})

        lowBand = activeODU['LowBand']
        highBand = activeODU['HighBand']
        
#First let's check if frequencies of the main and the alternative carrier from the config fits in the active LNB frequency range
        a = mainCarrier['Freq']
        if a:
            if ((lowBand['RFStart'] and a < lowBand['RFStart']) or (highBand['RFStop'] and a > highBand['RFStop'])) or \
               (lowBand['RFStop'] and a > lowBand['RFStop'] and (a < highBand['RFStart'] if highBand['RFStart'] else True)) or \
               (not lowBand['RFStop'] and highBand['RFStart'] and a < highBand['RFStart']):
                logger.warning('Main frequency is out of active ODU range')
                return False

        a = altCarrier['Freq']
        if a:
            if ((lowBand['RFStart'] and a < lowBand['RFStart']) or (highBand['RFStop'] and a > highBand['RFStop'])) or \
               (lowBand['RFStop'] and a > lowBand['RFStop'] and (a < highBand['RFStart'] if highBand['RFStart'] else True)) or \
               (not lowBand['RFStop'] and highBand['RFStart'] and a < highBand['RFStart']):
                logger.warning('Alternative frequency is out of active ODU range')
                return False
        logger.info('All frequencies are inside LNB range for this terminal')

#Second let's get the active beam data to correct it
        reply = _SendJSONRequest(rest, url, 'GetActiveBeam')
        activeBeamId = reply['BeamId']
        beamId = {"BeamId": activeBeamId}
        beamData = _SendJSONRequest(rest, url, 'GetBeamData', beamId)
        beamData['BeamId'] = activeBeamId

#Third let's determine which carrier is the default one ('Main') and which will be alternative then, the same for Pointing carriers
        defaultInitialCarrier = beamData['DefaultInitialCarrier']
        if defaultInitialCarrier == 1:
            mainCarrierData = beamData['InitialCarrier1']
            altCarrierData  = beamData['InitialCarrier2']
        if defaultInitialCarrier == 2:
            mainCarrierData = beamData['InitialCarrier2']
            altCarrierData  = beamData['InitialCarrier1']

        defaultPointingCarrier = beamData['DefaultPointingCarrier']
        if defaultPointingCarrier == 1:
            mainPointingCarrier = beamData['PointingCarrier1']
            altPointingCarrier  = beamData['PointingCarrier2']
        if defaultPointingCarrier == 2:
            mainPointingCarrier = beamData['PointingCarrier2']
            altPointingCarrier  = beamData['PointingCarrier1']

#Forth let's correct the main carrier
        bMainChanged = False
        mainCarrierData['Enabled'] = mainCarrier['Enabled']
        if mainCarrier['Freq']:
            mainCarrierData['Freq'] = mainCarrier['Freq']
            bMainChanged = True
        if mainCarrier['SymbolRate']:
            mainCarrierData['SymbolRate'] = mainCarrier['SymbolRate']
            bMainChanged = True
        if mainCarrier['Polarization'] > -1:
            mainCarrierData['Polarization'] = mainCarrier['Polarization']
            bMainChanged = True
        if mainCarrier['TSMode']:
            mainCarrierData['TSMode'] = mainCarrier['TSMode']
            bMainChanged = True

#Fifth let's correct the alternative carrier
        if altCarrier['Enabled'] != 'NoChange':
            altCarrierData['Enabled'] = altCarrier['Enabled']
        else: altCarrier['Enabled'] = altCarrierData['Enabled'] 
        if altCarrier['Freq']:
            altCarrierData['Freq'] = altCarrier['Freq']
        else:
            altCarrierData['Freq'] = mainCarrierData['Freq']
        if altCarrier['SymbolRate']:
            altCarrierData['SymbolRate'] = altCarrier['SymbolRate']
        else:
            altCarrierData['SymbolRate'] = mainCarrierData['SymbolRate']
        if altCarrier['Polarization'] > -1:
            altCarrierData['Polarization'] = altCarrier['Polarization']
        else:
            altCarrierData['Polarization'] = mainCarrierData['Polarization']
        if altCarrier['TSMode']:
            altCarrierData['TSMode'] = altCarrier['TSMode']
        else:
            altCarrierData['TSMode'] = mainCarrierData['TSMode']

#Sixth let's correlate the pointing carriers
        if mainCarrier['copyToPointingCarrier']:
            mainPointingCarrier['Carrier'] = mainCarrierData
        if altCarrier['copyToPointingCarrier']:
            altPointingCarrier['Carrier'] = altCarrierData

#Seventh let's send the data back to the modem and examine the reply
        print(beamData)
        logger.info('Sending data to the modem')
        reply = _SendJSONRequest(rest, url, 'SetBeamData', beamData)
        if bMainChanged:
            reply = True
        if reply and pauseAfterChange:
            logger.debug('Pause for %i seconds after data change' % pauseAfterChange)
            try:
                sleep(pauseAfterChange)
            except KeyboardInterrupt:
                exit(1)
        if reply and reboot:
            logger.info('Rebooting the modem')
            reply = _SendJSONRequest(rest, url, 'Reboot')
            if reply and pauseAfterReboot:
                logger.debug('Pause for %i seconds after reboot' % pauseAfterReboot)
                try:
                    sleep(pauseAfterReboot)
                except KeyboardInterrupt:
                    exit(1)
        if reply and checkAfterChange:
            logger.info('Checking if the modem has accepted the new settings')
            reply = _SendJSONRequest(rest, url, 'GetBeamData', beamId)
            if reply['DefaultInitialCarrier'] == 1:
                mainCarrierDataNew = reply['InitialCarrier1']
                altCarrierDataNew  = reply['InitialCarrier2']
            if reply['DefaultInitialCarrier'] == 2:
                mainCarrierDataNew = reply['InitialCarrier2']
                altCarrierDataNew  = reply['InitialCarrier1']
            result = (mainCarrierDataNew, altCarrierDataNew, airmac)
    except (TypeError, KeyError):
        result = False
    
    return result
