
Distributed Computing demo using pyzmq
====

This project demonstrates building a distributed project from scratch. It's
really intriguing.

It's not just heartbeat now. This project involves distributed computing (in my
scenario, judging), aliveness testing (the heartbeat thing) and something else.

Firstly, we have a master node, which has a node table (a dict), a command
socket (PULL-typed, whatever message will be pumped into this socket), a
heartbeat daemon socket (PUSH-typed, used for pushing current node table), and
we have a while-loop (which basically is an event-loop). In the event-loop, we
first destruct a message packet (a dict), and find out what **action** it is and
we execute the `if` sections accordingly.

A _message packet_ contains an **action**, and whatever parameters the **action**
needs.

Secondly, we have a heartbeat daemon (`show.py`), which requests for the table of
nodes alive and tests their aliveness every 5 seconds. Once a node is down (one
that does not reply 'heartbeat' message packet in 3 seconds), this node is
removed from the table on master node.

Thirdly, we have a task initiator. This initiator connects to master node via a
PUSH-typed socket and listens on a random local port with a PAIR-typed socket.
The initiator pushes task (i.e. judge request) through the PUSH-typed socket. The
master node will randomly choose a slave node to handle the request. If no node
is alive, the master node will connect to the PAIR-typed socket and send error
message packet. When a slave node finishes the job, it connects to the PAIR-typed
socket and sends `judge ret` message packet. Thus a job is done by now.

Finally, when a slave node is on (i.e. `slave.py` is executed, and it does not
care whether there are multiple instances of `slave.py`), it will send an `up`
message packet to the master node, notifying it being online. Slave nodes open on
random port a PULL-typed socket for tasks receiving uses, one PUSH-typed socket
for master communication. Once the master node receives the `up` message packet,
it connects to the PULL-typed socket and save the connected socket to another
table for future uses.

On job arriving, the slave node selected uses a process pool to call
asynchronizedly `judge_all.exe` (i.e. actually doing the judge task). When a job
is done on a slave node, it notifies the result by directly connecting to the
task initiator (whose address is given in the `judge` message packet), and sends
the result as a `judge ret` message packet or a `judge ret error` if anything
goes wrong.


Possible Problems
----

The problem I am now concerned about is what happens when a task is delivered
to a node, which, at that exact moment, went down.

Possible solution: check the aliveness of the node selected before actually
delivering the task; however, this may not turn out useful
