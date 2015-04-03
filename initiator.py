
l = 1
u = 1
s = '/home/wo/woj/temp/1/1.c'
n = 1001
D = '/home/wo/woj/data/1001'
d = '/home/wo/woj/temp/1'
t = 1000
m = 65536
o = 8192
S = False
c = '/home/wo/land/code/judge/langs'
p = '/home/wo/land/code/judge/pygent_path'

import zmq
from utils import msg as msg_, get_local_ip, MASTER_IP


local_ip = get_local_ip()

if __name__ == '__main__':
    ctx = zmq.Context()
    sck = ctx.socket(zmq.PAIR)
    port = sck.bind_to_random_port('tcp://%s' % local_ip)
    print('bound to tcp://%s:%s' % (local_ip, port))

    master_sck = ctx.socket(zmq.PUSH)
    master_sck.connect('tcp://%s:%s' % (MASTER_IP, 5555))
    print('connected to tcp://%s:%s' % (MASTER_IP, 5555))

    master_sck.send_json(msg_(act='judge',
                              args={'l': l, 'u': u, 's': s, 'n': n,
                                    'D': D, 'd': d, 't': t, 'm': m,
                                    'o': o, 'S': S, 'c': c, 'p': p},
                              addr='tcp://%s:%s' % (local_ip, port)))

    ret = sck.recv_json()

    assert 'act' in ret
    act = ret['act']
    if act == 'judge ret':
        print(ret['result'])
    elif act == 'judge ret error':
        print('14 0 0')
    else:
        print('14 -1 -1')
