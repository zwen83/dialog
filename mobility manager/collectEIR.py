import json, urllib2, base64


nmsurl = properties.get("dialog.rest.url")
dmmurl = properties.get("dmm.rest.url")
username = properties.get("dialog.rest.user")
password = properties.get("dialog.rest.password")

def queryLastFromTsdb(ipaddress,series,field,key,keyvalue):
    """
    queries the tsdb REST API at 'ipaddress' for the maximum value of 
    'field' over the 'period' for 'series' of modem with 
    'terminalID' and returns this maximum
    """
    query='SELECT LAST(\"'+field+'\") FROM \"'+series+ '\" WHERE \"'+key+'\"=\''+keyvalue+ '\''
    #print query
    collectmethod ='/query?db=telegraf&q='+urllib2.quote(query)
    #because this part of the url contains quotes, double quotes and spaces
    #we need to encode them with urllib.quote (replaces these chars with escape sequences)
    collecturl = 'http://'+ str(ipaddress)+':8086'+collectmethod
    #print collecturl
    request = urllib2.Request(collecturl)
    connection = urllib2.urlopen(request)
    result = json.load(connection)
    # result
    try:
        last = result["results"][0]["series"][0]["values"][0][1]
    except :
        last = None
        pass
    return last   
    
def geteirshapingratios(nmsurl,base64string):
    """
    queries NMS REST APIfor total CIR's of fwd and rtn pools.
    returns lists of all link ids  and list of cirs
    """
    collectmethod = '/satellite-network/collect?property=forwardLinkId&property=returnLinkId&property=beamId&property=id'  
    collecturl =nmsurl + collectmethod
    request = urllib2.Request(collecturl)
    request.add_header("Authorization", "Basic %s" % base64string)
    connection = urllib2.urlopen(request)
    satnets = json.load(connection)
    collectmethod = '/forward-pool/collect?property=id&property=forwardLinkId&type=TRANSPORT_BASED'  
    collecturl =nmsurl + collectmethod
    request = urllib2.Request(collecturl)
    request.add_header("Authorization", "Basic %s" % base64string)
    connection = urllib2.urlopen(request)
    fwdpools = json.load(connection)
    fwdpoolids={}
    fwdeirshapingratios = {}
    for fwdpool in fwdpools:
        fwdid =fwdpool['forwardLinkId']['systemId']
        fwdpoolids[fwdid ]= fwdpool['id']['systemId']
    #print fwdpoolids
    collectmethod = '/hub-module/collect?property=ipAddresses&satelliteNetworkId=' 
    series =  "forward.shaper.pools"
    key = "forward_pool_name"
    field = "eir_shaping_ratio"
    for satnet in satnets:
        satnetid = satnet['id']['systemId']
        collecturl =nmsurl+ collectmethod + str(satnetid)
        request = urllib2.Request(collecturl)
        request.add_header("Authorization", "Basic %s" % base64string)
        connection = urllib2.urlopen(request)
        result = json.load(connection)
        tsdbaddress = result[0]['ipAddresses'][0]
        beamname = satnet['beamId']['name']
        fwdid = satnet['forwardLinkId']['systemId']
        try:
            poolid = fwdpoolids[fwdid]
            keyvalue = 'forwardpool_'+str(poolid)
            fwdeirshapingratio = queryLastFromTsdb(tsdbaddress,series,field,key,keyvalue)
            fwdeirshapingratios[beamname]=fwdeirshapingratio
        except:
            fwdeirshapingratios[beamname]=None
            pass
    return fwdeirshapingratios

        

base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
            

fwdeirshapingratios=geteirshapingratios(nmsurl,base64string)

#print fwdeirshapingratios


for beam in beams:
    id = beam.getId()
    try :
        fwdeirshapingratio = fwdeirshapingratios[id]
    except :
        fwdeirshapingratio = None
        pass
        
    if fwdeirshapingratio != None:
        beam.setParameterValue('fwdeirshapingratiol',fwdeirshapingratio )

    else:
        beam.setParameterValue('fwdeirshapingratiol',-1000)
    print 'beam ', id,' fwd eir shaping ratio=',fwdeirshapingratio
 


    
