from utils import logger

logger = logger()

debug_ = logger.debug
info_ = logger.info
warning_ = logger.warning
critical_ = logger.critical
error_ = logger.error

port = 21557

import zmq
from time import sleep
from utils import msg as msg_, unpack_ret, MASTER_IP, get_local_ip

ctx = zmq.Context()

msg_sck = ctx.socket(zmq.PULL)
msg_sck.setsockopt(zmq.RCVTIMEO, 3000)
msg_sck.bind('tcp://%s:21557' % get_local_ip())
debug_('bound to %s successfully', port)

master_sck = ctx.socket(zmq.PUSH)
master_sck.connect('tcp://%s:5555' % MASTER_IP)

poller = zmq.Poller()
poller.register(msg_sck, zmq.POLLIN)

while True:
    info_('heartbeat daemon alive')

    master_sck.send_json(msg_('list nodes'))
    debug_('list nodes sent')

    try:
        msg = msg_sck.recv_json()
    except zmq.error.Again:
        critical_('Master seems DOWN.')
        break

    assert 'act' in msg

    if msg['act'] == 'check aliveness now':
        master_sck.send_json(msg_('list nodes'))
        continue
    elif msg['act'] == 'ret':
        status, payload = unpack_ret(msg)
        if status == 'list nodes ok':
            if not payload:
                info_('no nodes alive')

            for node in payload:

                info_('attempting %s', node)

                _s = ctx.socket(zmq.PUSH)
                _s.connect(node)
                debug_('connected to %s', node)

                _s.send_json(msg_('heartbeat'))
                debug_('sent heartbeat')
                _s.close()

                if poller.poll(3 * 1000):
                    ret = msg_sck.recv_json()
                    if ret['act'] == 'ret':
                        status, payload = unpack_ret(ret)
                        debug_(payload)
                        if status == 'ok':
                            if payload['msg'] == '<3':
                                if payload['addr'] == node:
                                    # ok
                                    info_('%s heartbeat normal', node)
                                    continue

                warning_('%s %s', node, 'down')
                master_sck.send_json(msg_('down', addr=node))

    sleep(5)
