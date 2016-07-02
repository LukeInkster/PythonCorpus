Kinesis Example
===========================

![gordon](https://gordon.readthedocs.io/en/latest/_static/examples/kinesis.svg)

This simple project defines one lambda called ``kinesisconsumer`` and integrates it with one kinesis stream.

Every time one change is published to the stream, the lambda will be executed.

The lambda is quite dumb, and only prints the received event.


Documentation relevant to this example:
 * [Lambdas](https://gordon.readthedocs.io/en/latest/lambdas.html)
 * [Kinesis](https://gordon.readthedocs.io/en/latest/eventsources/kinesis.html)

How to deploy it?
------------------

* Create a Kinesis stream and get the ARN by running:
 * ``$ aws kinesis describe-stream --stream-name NAME``
* ``$ gordon build``
* ``$ gordon apply``
* Send a test message to your kinesis by doing:
 * ``$ aws kinesis put-record --stream-name gordon-test  --partition-key 123 --data hello``
