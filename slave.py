
import sys
import utils
import multiprocessing
import subprocess
import time
import random

msg_ = utils.msg
unpack_ret = utils.unpack_ret
logger = utils.logger()
MASTER_IP = utils.MASTER_IP
HEARTBEAT_DAEMON_IP = utils.HEARTBEAT_DAEMON_IP

debug_ = logger.debug
info_ = logger.info
warning_ = logger.warning
critical_ = logger.critical
error_ = logger.error

master_ip_port = '%s:5555' % MASTER_IP

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


master_sck = ctx.socket(zmq.PUSH)
master_sck.connect('tcp://%s' % master_ip_port)
debug_('connected to master successful')
master_sck.send_json(msg_('up', addr='tcp://%s:%s' % (local_ip, port)))
info_('send up successful')

def target(args):
    return subprocess.check_output(['./test'])

pool = multiprocessing.Pool(maxtasksperchild=15)
while True:
    task = task_sck.recv_json()

    assert 'act' in task
    act = task['act']

    if act == 'heartbeat':
        time.sleep(random.randint(0, 2))

        hd_sck = ctx.socket(zmq.PAIR)
        hd_sck.connect('tcp://192.168.1.112:%s' % task['port'])
        hd_sck.send_json(msg_('ret',
                              status='ok',
                              payload={'addr': 'tcp://%s:%s' % (local_ip,
                                                                port),
                                       'msg': '<3'}))
        debug_('heartbeat at %s:%s', local_ip, port)
    elif act == 'ret':
        status, payload = unpack_ret(task)
        if task['status'] == 'ok':
            info_('master responsed %s', payload)
    elif act == 'judge':
        info_('judge task received')

        args = task['args']
        initiator_addr = task['addr']

        def callback(result):
            initiator_sck = ctx.socket(zmq.PAIR)
            initiator_sck.connect(initiator_addr)
            initiator_sck.send_json(msg_(act='judge ret',
                                         result=str(result)))
            initiator_sck.close()

        def error_callback(error_result):
            initiator_sck = ctx.socket(zmq.PAIR)
            initiator_sck.connect(initiator_addr)
            initiator_sck.send_json(msg_(act='judge ret error',
                                         result=str(error_result)))
            initiator_sck.close()

        pool.apply_async(target, args=(args,),
                         callback=callback,
                         error_callback=error_callback)

    else:
        warning_('unable to act, message not understandable')
