# cfn-extras
CloudFormation sometimes lags behind new feature releases. boto3 is usually updated quickly. This repo is for a series of custom cloudformation resources to do things like PrivateLink. 

The methodology is to use Lambda functions. 

# private-link
    Example of a private link
    Type: Custom::PrivateLink
    Properties:
      ServiceToken: ARN of Lambda
      vpcId: mandatory; valid VPC ID
      serviceName: Mandtory; must be a valid service
      subnets:
        - optional
      securityGroups:
        - optional
      routeTableIds:
        - optional