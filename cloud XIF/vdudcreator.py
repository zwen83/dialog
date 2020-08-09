print("Enter the number of satnets you want to deploy.")
totalhpsstr = input()
totalhps = int(totalhpsstr)

## CHANGE THE FOLLOWING PARAM TO THE NUMBER OF SATNET YOU WISH TO DEPLOY IT HARDCODED
##totalhps = 13

##DONT CHANGE BELLOW CODE##############################
#######################################################
currenthpsid = 0
totalhpspool = 0
currenthpspoolid =0

#instantiate the hps pools based on the number of hps
if totalhps <= 6 :
 totalhpspool= 1
elif totalhps <= 12 :
 totalhpspool = 2
elif totalhps <= 18 :
 totalhpspool = 3
else: print("Illegal number of hps, you cannot deploy more than 18 hps exiting code") and exit

print ("The total number of hps is: ")
print(totalhps)

print ("The total number of hpspools is: ")
print (totalhpspool)

#create vdudfile
file = open("vdud.yaml","w+")

def printBSC(poolid, redundancyid):
    file.write("BSC-" + str(poolid) + "-" + str(redundancyid) + ":" + "\n")
    file.write("  VNF: BSC" + "\n")
    file.write("  SRV_GROUP: BSC-" + str(poolid) + "\n")
    file.write("  HOSTNAME: BSC-" + str(poolid) + "-" + str(redundancyid) + "\n")
    file.write("  METADATA:" + "\n")
    file.write("    ntc-dialog-set-hubmoduleid: {get_input: PROCHUBMODULEID}" + "\n")
    file.write("    ntc-dialog-set-hmtype: {get_input: HMTYPE}" + "\n")
    file.write("    ntc-dialog-set-sap-vip: {get_input: HMGW-" + str(poolid) + "-0-SAP}" + "\n")
    file.write("    ntc-dialog-set-sap-ip-1: {get_input: HMGW-" + str(poolid) + "-1-SAP}" + "\n")
    file.write("    ntc-dialog-set-sap-ip-2: {get_input: HMGW-" + str(poolid) + "-2-SAP}" + "\n")
    file.write("    ntc-dialog-set-cms-vip: {get_input: CMS-0-SAP}" + "\n")
    file.write("    ntc-dialog-set-sap-netmask: {get_input: SAP-NETMASK}" + "\n")
    file.write("    ntc-dialog-set-sap-defgw: {get_input: SAP-GATEWAY}" + "\n")
    file.write("  CP1:" + "\n")
    lastipocted = 231 + ((poolid * 4) + redundancyid)
    file.write("    ipaddress: 172.20.0." + str(lastipocted) + "\n")

def printlog(poolid, redundancyid):
    file.write("LOG-" + str(poolid) + "-" + str(redundancyid) + ":" + "\n")
    file.write("  VNF: LOG" + "\n")
    file.write("  SRV_GROUP: LOG-" + str(poolid) + "\n")
    file.write("  HOSTNAME: LOG-" + str(poolid) + "-" + str(redundancyid) + "\n")
    file.write("  CP1:" + "\n")
    lastipocted = 61 + ((poolid * 3) + redundancyid)
    file.write("    ipaddress: 172.20.0." + str(lastipocted) + "\n")

def printmon(poolid, redundancyid):
    file.write("MON-" + str(poolid) + "-" + str(redundancyid) + ":" + "\n")
    file.write("  VNF: MON" + "\n")
    file.write("  SRV_GROUP: MON-" + str(poolid) + "\n")
    file.write("  HOSTNAME: MON-" + str(poolid) + "-" + str(redundancyid) + "\n")
    file.write("  CP1:" + "\n")
    lastipocted = 71 + ((poolid * 3) + redundancyid)
    file.write("    ipaddress: 172.20.0." + str(lastipocted) + "\n")

def printhmgw(poolid, redundancyid):
    file.write("HMGW-" + str(poolid) + "-" + str(redundancyid) + ":" + "\n")
    file.write("  VNF: HMGW" + "\n")
    file.write("  SRV_GROUP: HMGW-" + str(poolid) + "\n")
    file.write("  HOSTNAME: HMGW-" + str(poolid) + "-" + str(redundancyid) + "\n")
    file.write("  CP1:" + "\n")
    lastipocted = 31 + ((poolid * 3) + redundancyid)
    file.write("    ipaddress: 172.20.0." + str(lastipocted) + "\n")

def printredctl(poolid, redundancyid):
    file.write("REDCTL-" + str(poolid) + "-" + str(redundancyid) + ":" + "\n")
    file.write("  VNF: REDCTL" + "\n")
    file.write("  SRV_GROUP: REDCTL-" + str(poolid) + "\n")
    file.write("  HOSTNAME: REDCTL-" + str(poolid) + "-" + str(redundancyid) + "\n")
    file.write("  CP1:" + "\n")
    lastipocted = 41 + ((poolid * 3) + redundancyid)
    file.write("    ipaddress: 172.20.0." + str(lastipocted) + "\n")

def printtcs(hpsid, redundancyid):
    file.write("TCS-" + str(hpsid) + "-" + str(redundancyid) + ":" + "\n")
    file.write("  VNF: TCS" + "\n")
    file.write("  SRV_GROUP: TCS-" + str(hpsid) + "\n")
    file.write("  HOSTNAME: TCS-" + str(hpsid) + "-" + str(redundancyid) + "\n")
    file.write("  CP1:" + "\n")
    lastipocted = 51 + redundancyid
    file.write("    ipaddress: 172.20." + str(hpsid) + "." + str(lastipocted) + "\n")

def printpgicse(hpsid):
    file.write("PGICSE-" + str(hpsid) + ":" + "\n")
    file.write("  VNF: CSE" + "\n")
    file.write("  SRV_GROUP: CSE-" + str(hpsid) + "\n")
    file.write("  HOSTNAME: PGICSE-" + str(hpsid) + "\n")
    file.write("  CP1:" + "\n")
    thirdipocted = 200 + hpsid
    file.write("    ipaddress: 172.20." + str(thirdipocted) + "." + "30" + "\n")

def printpgidcp(hpsid):
    file.write("PGIDCP-" + str(hpsid) + ":" + "\n")
    file.write("  VNF: DCP" + "\n")
    file.write("  SRV_GROUP: DCP-" + str(hpsid) + "\n")
    file.write("  HOSTNAME: PGIDCP-" + str(hpsid) + "\n")
    file.write("  CP1:" + "\n")
    thirdipocted = 200 + hpsid
    file.write("    ipaddress: 172.20." + str(thirdipocted) + "." + "120" + "\n")

def printpgicpmctl(hpsid):
    file.write("PGICPMCTL-" + str(hpsid) + ":" + "\n")
    file.write("  VNF: CPMCTL" + "\n")
    file.write("  SRV_GROUP: CPMCTL-" + str(hpsid) + "\n")
    file.write("  HOSTNAME: PGICPMCTL-" + str(hpsid) + "\n")
    file.write("  CP1:" + "\n")
    thirdipocted = 200 + hpsid
    file.write("    ipaddress: 172.20." + str(thirdipocted) + "." + "70" + "\n")

def printpgihrcctl(hpsid):
    file.write("PGIHRCCTL-" + str(hpsid) + ":" + "\n")
    file.write("  VNF: HRCCTL" + "\n")
    file.write("  SRV_GROUP: HRCCTL-" + str(hpsid) + "\n")
    file.write("  HOSTNAME: PGIHRCCTL-" + str(hpsid) + "\n")
    file.write("  CP1:" + "\n")
    thirdipocted = 200 + hpsid
    file.write("    ipaddress: 172.20." + str(thirdipocted) + "." + "80" + "\n")

def printpgis2xctl(hpsid):
    file.write("PGIS2XCTL-" + str(hpsid) + ":" + "\n")
    file.write("  VNF: S2XCTL" + "\n")
    file.write("  SRV_GROUP: S2XCTL-" + str(hpsid) + "\n")
    file.write("  HOSTNAME: PGIS2XCTL-" + str(hpsid) + "\n")
    file.write("  CP1:" + "\n")
    thirdipocted = 200 + hpsid
    file.write("    ipaddress: 172.20." + str(thirdipocted) + "." + "90" + "\n")

def printpgitas(hpsid):
    file.write("PGITAS-" + str(hpsid) + ":" + "\n")
    file.write("  VNF: TAS" + "\n")
    file.write("  SRV_GROUP: TAS-" + str(hpsid) + "\n")
    file.write("  HOSTNAME: PGITAS-" + str(hpsid) + "\n")
    file.write("  CP1:" + "\n")
    thirdipocted = 200 + hpsid
    file.write("    ipaddress: 172.20." + str(thirdipocted) + "." + "10" + "\n")


def printpgidem(hpsid):
    file.write("PGIDEM-" + str(hpsid) + ":" + "\n")
    file.write("  VNF: L3DEM" + "\n")
    file.write("  SRV_GROUP: DEM-" + str(hpsid) + "\n")
    file.write("  HOSTNAME: PGIDEM-" + str(hpsid) + "\n")
    file.write("  CP1:" + "\n")
    thirdipocted = 200 + hpsid
    file.write("    ipaddress: 172.20." + str(thirdipocted) + "." + "240" + "\n")


def printpgideml2(hpsid):
    file.write("PGIL2DEM-" + str(hpsid) + ":" + "\n")
    file.write("  VNF: PGIL2DEM-" + str(hpsid) + "\n")
    file.write("  SRV_GROUP: L2DEM-" + str(hpsid) + "\n")
    file.write("  HOSTNAME: PGIL2DEM-" + str(hpsid) + "\n")
    file.write("  CP1:" + "\n")
    thirdipocted = 200 + hpsid
    file.write("    ipaddress: 172.20." + str(thirdipocted) + "." + "220" + "\n")


def deployhpspoolmachines():
    for x in range (0, totalhpspool):
        print("defining hpspoolmachines (BSC, log, mon, hmgw, redctl for hpspool: " + str(x))
        currenthpspoolid = x
        printBSC(currenthpspoolid, 1)
        printBSC(currenthpspoolid, 2)
        printlog(currenthpspoolid, 1)
        printlog(currenthpspoolid, 2)
        printmon(currenthpspoolid, 1)
        printmon(currenthpspoolid, 2)
        printhmgw(currenthpspoolid, 1)
        printhmgw(currenthpspoolid, 2)
        printredctl(currenthpspoolid, 1)
        printredctl(currenthpspoolid, 2)

def deploytcsmachines():
    hpsflag = 0
    for x in range (1, totalhps+1):
        currenthpsid = x + hpsflag
        print("defining tcs machines " + str(currenthpsid))
        printtcs(currenthpsid, 1)
        printtcs(currenthpsid, 2)

        if currenthpsid == 6:
            hpsflag = hpsflag + 1
        if currenthpsid == 13:
            hpsflag = hpsflag + 1

def deploytrafficprocessingmachines():
    for x in range (1, totalhps+1):
        print("defining traffic processing machines cse, dcp, cpmctl, hrcctl, s2xctl, tas, dem, l2dem for hps: " + str(x))
        currenthpsid = x
        printpgicse(currenthpsid)
        printpgidcp(currenthpsid)
        printpgicpmctl(currenthpsid)
        printpgihrcctl(currenthpsid)
        printpgis2xctl(currenthpsid)
        printpgitas(currenthpsid)
        printpgidem(currenthpsid)
        printpgideml2(currenthpsid)

    for x in range(1, totalhpspool+1):
        currenthpsid += 1
        print("defining redundant traffic processing machines (1 per hpspool) devices: " + str(currenthpsid))
        printpgicse(currenthpsid)
        printpgidcp(currenthpsid)
        printpgicpmctl(currenthpsid)
        printpgihrcctl(currenthpsid)
        printpgis2xctl(currenthpsid)
        printpgitas(currenthpsid)
        printpgidem(currenthpsid)
        printpgideml2(currenthpsid)

deployhpspoolmachines()
deploytcsmachines()
deploytrafficprocessingmachines()
