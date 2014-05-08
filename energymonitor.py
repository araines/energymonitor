import sys, socket, re
from pyrrd.rrd import DataSource, RRA, RRD
from pyrrd.graph import DEF, LINE, GPRINT, Graph

RRD_IMAGES_LOCATION  = '/www/rrdtool'

def get_energy():
	tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	tx_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	tx_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	tx_sock.settimeout(2.0)

	rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	rx_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	rx_sock.settimeout(2.0)
	rx_sock.bind(('0.0.0.0', 9761))

	msg = '100,@?W'
	tx_sock.sendto(msg, ('255.255.255.255', 9760))
	data = rx_sock.recv(1024)

	valid    = re.compile(r'^\d{1,3},\?W=([0-9,]+)\r\n$')
	match    = valid.match(data)
	if match:
		power = match.group(1).split(',')
		return {
			'current':          power[0],
			'max_today':        power[1],
			'total_today':      power[2],
			'total_yesterday':  power[3],
		}
	return None

def get_rrd_database():
	# TODO: Load from existing file
	print ("Creating RRD database for power")
	dss  = []
	rras = []
	dss.append(DataSource(dsName='power', dsType='GAUGE'))
	rras.append(RRA(cf='AVERAGE', xff=0.5, steps=1,   rows=576))
	rras.append(RRA(cf='AVERAGE', xff=0.5, steps=6,   rows=672))
	rras.append(RRA(cf='AVERAGE', xff=0.5, steps=24,  rows=732))
	rras.append(RRA(cf='AVERAGE', xff=0.5, steps=144, rows=1460))

	rrd = RRD('/www/rrdtool/power.rrd', ds=dss, rra=rras)
	rrd.create()

	return rrd

def process_energy():
	energy = get_energy()

	print ("Current energy usage: %s" % energy)

	rrd = get_rrd_database()

	# insert value into rrd
	rrd.bufferValue('N:%s' % energy['current'])

	# create graphs
	create_graph(rrd, 'day')
	create_graph(rrd, 'week')
	create_graph(rrd, 'month')
	create_graph(rrd, 'year')

def create_graph(rrd, interval):
	def1  = DEF(rrdfile=rrd.filename, vname='Power', dsName='power')
	line1 = LINE(defObj=def1, color='#0000FF', legend='Power Used')
	g     = Graph('/www/rrdtool/power.png')
	g.data.extend([def1, line1])
	g.write()
