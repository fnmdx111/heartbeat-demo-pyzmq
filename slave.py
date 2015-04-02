
import sys
import utils

msg_ = utils.msg
unpack_ret = utils.unpack_ret
logger = utils.logger()

debug_ = logger.debug
info_ = logger.info
warning_ = logger.warning
critical_ = logger.critical
error_ = logger.error

master_ip_port = '192.168.1.102:5555'

try:
    port = sys.argv[2]
except IndexError:
    port = None

local_ip = utils.get_local_ip()

import zmq
ctx = zmq.Context()

task_sck = ctx.socket(zmq.PULL)
port = port or task_sck.bind_to_random_port('tcp://%s' % local_ip)
debug_('bound successfully to %s:%s', local_ip, port)

hd_sck = ctx.socket(zmq.PUSH)
hd_sck.connect('tcp://192.168.1.102:21557')
debug_('connected to heartbeat daemon')

master_sck = ctx.socket(zmq.PUSH)
master_sck.connect('tcp://%s' % master_ip_port)
debug_('connected to master successful')
master_sck.send_json(msg_('up', addr='tcp://%s:%s' % (local_ip, port)))
info_('send up successful')


while True:
    task = task_sck.recv_json()

    assert 'act' in task
    act = task['act']

    if act == 'heartbeat':
        hd_sck.send_json(msg_('ret',
                              status='ok',
                              payload={'addr': 'tcp://%s:%s' % (local_ip, port),
                                       'msg': '<3'}))
        debug_('heartbeat at %s:%s', local_ip, port)
    elif act == 'ret':
        status, payload = unpack_ret(task)
        if task['status'] == 'ok':
            info_('master responsed %s', payload)
    else:
        warning_('unable to act, message not understandable')
