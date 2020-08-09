from influxdb import InfluxDBClient
import threading

# opt=input("\n\nWhich module you would like to run tsdb checks?1.CMS \n2.BHI \n3.JAV \n4.SUB\n\n\n\nEnter 1 or 2 or 3 or 4: ")


def gw_check(iplist,fout):
	for ip in iplist:
		try:
			client = InfluxDBClient(host=ip, database='telegraf')
			result1=client.query('''select * from "modem.forward.S2" where time > now()-2m limit 2''')
		# with open(r"tsdb_BHI_check.txt", mode="a+") as fs:
		# 	fs.write("\n\nTSDB modem fwd stats\n\n")
		# 	fs.write(str(result1))
			result2=client.query('''select * from "modem.return.cpm_generic" where time > now()-2m limit 2''')
		# with open(r"tsdb_BHI_check.txt", mode="a+") as fs:
		# 	fs.write("\n\nTSDB modem return cpm stats\n\n")
		# 	fs.write(str(result2))
			result3=client.query('''select * from "modem.return.hrc_generic" where time > now()-2m limit 2''')
		# with open(r"tsdb_BHI_check.txt", mode="a+") as fs:
		# 	fs.write("\n\nTSDB modem hrc stats\n\n")
		# 	fs.write(str(result3))
			result4=client.query('''select * from "return.decapsulator" where time > now()-2m limit 2''')
		# with open(r"tsdb_BHI_check.txt", mode="a+") as fs:
		# 	fs.write("\n\nTSDB modem decap stats\n\n")
		# 	fs.write(str(result4))
			result5=client.query('''select * from "forward.shaper" where time > now()-2m limit 2''')
			print(list(result5))
			with open(fout, mode="a+") as fs:
				td="Checking the tsdb for HMGW IP:" + ip
				fs.write("\n\n")
				fs.write(td)
				fs.write("\n\nTSDB modem fwd stats\n\n")
				fs.write(str(result1))
				fs.write("\n\nTSDB modem return cpm stats\n\n")
				fs.write(str(result2))
				fs.write("\n\nTSDB modem hrc stats\n\n")
				fs.write(str(result3))
				fs.write("\n\nTSDB modem decap stats\n\n")
				fs.write(str(result4))
				fs.write("\n\nTSDB modem cse stats\n\n")
				fs.write(str(result5))
		except:
			pass


def NMS():
	client = InfluxDBClient(host='10.0.10.60', database='telegraf')
	result1=client.query('''select * from "cpu" where time > now()-2m limit 2''')
	# print(list(result1))
	# print(type(result1))
	with open(r"tsdb_check_NMS.txt", mode="a+") as fs:
		fs.write("\n\nTSDB cpu stats\n\n")
		fs.write(str(result1))
	result2=client.query('''select * from "disk" where time > now()-2m limit 2''')
	with open(r"tsdb_check_NMS.txt", mode="a+") as fs:
		fs.write("\n\nTSDB disk stats\n\n")
		fs.write(str(result2))
	result3=client.query('''select * from "diskio" where time > now()-2m limit 2''')
	with open(r"tsdb_check_NMS.txt", mode="a+") as fs:
		fs.write("\n\nTSDB diskio stats\n\n")
		fs.write(str(result3))
	result4=client.query('''select * from "system" where time > now()-2m limit 2''')
	with open(r"tsdb_check_NMS.txt", mode="a+") as fs:
		fs.write("\n\nTSDB system stats\n\n")
		fs.write(str(result4))
	result5=client.query('''select * from "netstat" where time > now()-2m limit 2''')
	with open(r"tsdb_check_NMS.txt", mode="a+") as fs:
		fs.write("\n\nTSDB net stats\n\n")
		fs.write(str(result5))


if __name__ == '__main__':
	threading.Thread(target=NMS).start()

	BHI = ["10.25.10.180", "10.25.10.183", "10.25.10.186", "10.25.11.60", "10.25.11.63",]
	foutBHI = r"tsdb_check_bhi.txt"
	B = threading.Thread(target=gw_check,args=(BHI,foutBHI,))
	B.start()

	JAV = ["10.50.10.180", "10.50.11.183", "10.50.11.60", "10.50.11.63",]
	foutJAV = r"tsdb_check_jav.txt"
	J = threading.Thread(target=gw_check,args=(JAV,foutJAV,))
	J.start()

	SUB = ["10.75.10.180", "10.75.10.183", "10.75.11.60", "10.75.11.63",]
	foutSUB = r"tsdb_check_sub.txt"
	S = threading.Thread(target=gw_check,args=(SUB,foutSUB,))
	S.start()







