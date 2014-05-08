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
		os.system("rrdtool create %s     \
				-s 60                    \
				DS:power:GAUGE:120:U:U   \
				RRA:AVERAGE:0.5:1:10080  \
				RRA:AVERAGE:0.5:60:720   \
				RRA:AVERAGE:0.5:180:480  \
				RRA:AVERAGE:0.5:1440:730" % rrd_db)

	return rrd_db


def process_energy():
	energy = get_energy()

	print ("Current energy usage: %s" % energy)

	rrd = get_rrd_database()

	# insert value into rrd
	os.system("rrdtool update %s    \
			-t power                \
			N:%s" % (rrd, energy['current']))

	# create graphs
	create_graph(rrd, 'hour')
	create_graph(rrd, 'day')
	create_graph(rrd, 'week')
	create_graph(rrd, 'month')
	create_graph(rrd, 'year')

def create_graph(rrd, interval):
	os.system("rrdtool graph '/www/rrdtool/power-%s.png' \
			--lazy \
			-s -1%s \
			-t 'Power Usage (last %s)' \
			-h 160 \
			-w 600 \
			-a PNG \
			-v Watts \
			-l 0 \
			DEF:power=%s:power:AVERAGE \
			AREA:power#0000FF:Power \
			GPRINT:power:MIN:\"  Min\\: %%2.lf\" \
			GPRINT:power:MAX:\"  Max\\: %%2.lf\" \
			GPRINT:power:AVERAGE:\"  Avg\\: %%4.1lf\" \
			GPRINT:power:LAST:\" Current\\: %%2.lf Watts\\n\" \
			" % (interval, interval, interval, rrd))

if __name__ == "__main__":
	process_energy()
