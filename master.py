import sys
from utils import msg as msg_, logger, MASTER_IP, get_local_ip
import random as rd
import uuid

local_ip = get_local_ip()


try:
    port = sys.argv[2]
except IndexError:
    port = 5555

logger = logger()

debug_ = logger.debug
info_ = logger.info
warning_ = logger.warning
critical_ = logger.critical
error_ = logger.error


import zmq

ctx = zmq.Context()

cmd_sck = ctx.socket(zmq.PULL)

cmd_sck.bind('tcp://*:%s' % port)
debug_('bound to %s successful' % port)

hd_sck = ctx.socket(zmq.PUSH)
hd_sck.connect('tcp://%s:21557' % MASTER_IP)

nodes = {}
nodes_sockets = {}

poller = zmq.Poller()

while True:
    debug_('blocking when recv_json')
    msg = cmd_sck.recv_json()

    assert 'act' in msg
    action = msg['act']

    if action == 'up':
        addr = msg['addr']
        info_('addr %s up' % addr)
        nodes[addr] = 1
        _s = nodes_sockets[addr] = ctx.socket(zmq.PUSH)
        _s.setsockopt(zmq.SNDTIMEO, 3000)
        _s.connect(addr)
        _s.send_json(msg_('ret', status='ok', payload='ACK'))

    elif action == 'list nodes':
        info_('listing nodes %s', nodes)
        hd_sck.send_json(msg_('ret', status='list nodes ok', payload=nodes))

    elif action == 'judge':
        if not nodes:
            error_('all nodes down, we\'ve got no one to assign work to')
            initiator_sck = ctx.socket(zmq.PAIR)
            initiator_sck.connect(msg['addr'])
            initiator_sck.send_json(msg_(act='judge ret error',
                                         result='no living nodes'))
            initiator_sck.close()

            continue

        while True:
            distribution_target = rd.choice(list(nodes.keys()))
            rd_key = str(uuid.uuid4())
            info_('judge task received, distributing to %s, random key %s',
            distribution_target, rd_key)

            ns = nodes_sockets[distribution_target]

            ack_socket = ctx.socket(zmq.PAIR)
            ack_port = ack_socket.bind_to_random_port('tcp://%s' % local_ip)

            poller.register(ns, zmq.POLLOUT)
            poller.register(ack_socket, zmq.POLLIN)
            if poller.poll(3 * 1000):
                ns.send_json(msg_(act='judge',
                                  args=msg['args'],
                                  addr=msg['addr'],
                                  rd_key=rd_key,
                                  ack_port=ack_port))
                ack = ack_socket.recv_json()
                if ack['act'] == 'ack':
                    if ack['rd_key'] == rd_key:
                        # ok
                        break
                continue
            else:
                # ns send timeout
                continue

    elif action == 'down':
        addr = msg['addr']
        if addr in nodes:
            del nodes[addr]
        if addr in nodes_sockets:
            nodes_sockets[addr].close()
            del nodes_sockets[addr]
