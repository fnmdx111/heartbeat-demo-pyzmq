from utils import logger

logger = logger()

debug_ = logger.debug
info_ = logger.info
warning_ = logger.warning
critical_ = logger.critical
error_ = logger.error


import zmq
from time import sleep
from utils import msg as msg_, unpack_ret, get_local_ip
MASTER_ADDR = 'tcp://192.168.1.112:5555'
HEARTBEAT_DAEMON_PORT = '21557'


port = HEARTBEAT_DAEMON_PORT

local_ip = get_local_ip()


ctx = zmq.Context()

msg_socket = ctx.socket(zmq.PULL)
msg_socket.setsockopt(zmq.RCVTIMEO, 3000)
msg_socket.bind('tcp://%s:%s' % (local_ip, port))
debug_('bound to %s successfully', port)

master_socket = ctx.socket(zmq.PUSH)
master_socket.connect(MASTER_ADDR)

poller = zmq.Poller()
poller.register(msg_socket, zmq.POLLIN)

info_('heartbeat daemon alive')

def alive(node, poller):
    _s = ctx.socket(zmq.PAIR)
    _port = _s.bind_to_random_port('tcp://%s' % local_ip)
    poller.register(_s, zmq.POLLIN)

    inst_socket = ctx.socket(zmq.PUSH)
    inst_socket.connect(node)
    inst_socket.send_json(msg_('heartbeat', port=_port))
    debug_('sent heartbeat')
    inst_socket.close()

    if poller.poll(3 * 1000):
        ret = _s.recv_json()
        _s.close()

        if ret['act'] == 'ret':
            status, payload = unpack_ret(ret)
            debug_(payload)
            if status == 'ok':
                if payload['msg'] == '<3':
                    if payload['addr'] == node:
                        # ok
                        info_('%s heartbeat normal', node)

                        poller.unregister(_s)

                        return True

    return False


while True:
    master_socket.send_json(msg_('list nodes'))

    try:
        msg = msg_socket.recv_json()
    except zmq.error.Again:
        critical_('Master seems DOWN.')
        break

    assert 'act' in msg

    if msg['act'] == 'check aliveness now':
        master_socket.send_json(msg_('list nodes'))
        continue
    elif msg['act'] == 'ret':
        status, payload = unpack_ret(msg)
        if status == 'list nodes ok':
            if not payload:
                info_('no nodes alive')

            for node in payload:
                info_('attempting %s', node)

                if alive(node, poller):
                    continue

                warning_('%s %s', node, 'down')
                master_socket.send_json(msg_('down', addr=node))

    sleep(5)
