CloudFormation Custom Resource Example
========================================

This simple project defines one Lambda that once deployed, can be used as ``ServiceToken`` of your Custom CloudFormation resources.

You'll only need to deploy it and use the ``Arn``   as the ``ServiceToken`` of your resource.

```json
"MyCustomResource": {
  "Type": "Custom::MyCustomLambdaResource",
  "Properties": {
    "ServiceToken": { "Ref" : "CustomLambdaArn" }
  }
}
```

Documentation relevant to this example:
 * [Lambdas](https://gordon.readthedocs.io/en/latest/lambdas.html)
 * [AWS:Lambda-backed Custom Resources](http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources-lambda.html)

How to deploy it?
------------------

* ``$ gordon build``
* ``$ gordon apply``
