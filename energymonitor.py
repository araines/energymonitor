import sys, socket, re, time, os.path, os
#from pyrrd.rrd import DataSource, RRA, RRD
#from pyrrd.graph import DEF, LINE, GPRINT, Graph

RRD_DB_LOCATION      = '/www/rrdtool'
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
	rrd_db = '/www/rrdtool/power.rrd'
	if not os.path.isfile(rrd_db):

		print ("Creating RRD database for power")
		os.system("rrdtool create %s   \
				-s 300                 \
				DS:power:GAUGE:600:U:U \
				RRA:AVERAGE:0.5:1:576  \
				RRA:AVERAGE:0.5:6:672   \
				RRA:AVERAGE:0.5:24:732   \
				RRA:AVERAGE:0.5:144:1460" % rrd_db)


def process_energy():
	energy = get_energy()

	print ("Current energy usage: %s" % energy)

	rrd = get_rrd_database()

	# insert value into rrd
	rrd.bufferValue('%s:%s' % (int(time.time()), energy['current']))
	rrd.update(template='power')

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

if __name__ == "__main__":
	process_energy()
