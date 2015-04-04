How to play with this demo
====

Start `heartbeatd` by change directory and `./heartbeatd`.

Also start `master`.

Start as many `slave`s as you like. Remember to compile `slave/test.c`.

Start as many `initiator`s as you like, and pay attention to its output.

This demo mainly demonstrates a scenario where RPC tasks are being
distributed to multiple slave nodes, and the results of such tasks being
reported back to `initiator`s (i.e. clients).

