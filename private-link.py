import boto3 
import time
from botocore.vendored import requests
import json

SUCCESS = "SUCCESS"
FAILED = "FAILED"
 
EC2 = boto3.client('ec2')
CFN = boto3.client('cloudformation')
VALID_SERVICES = ['ec2','ec2messages','elasticloadbalancing','ssm','kms','servicecatalog','kinesis-streams']

#cloudformation custom resource plumbing, http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-lambda-function-code.html
def send(event, context, responseStatus, responseData, reason = None, physicalResourceId=None):
    responseUrl = event['ResponseURL']
    responseBody = {}
    responseBody['Status'] = responseStatus
    responseBody['Reason'] = reason or 'See the details in CloudWatch Log Stream: ' + context.log_stream_name
    responseBody['PhysicalResourceId'] = physicalResourceId or context.log_stream_name
    responseBody['StackId'] = event['StackId']
    responseBody['RequestId'] = event['RequestId']
    responseBody['LogicalResourceId'] = event['LogicalResourceId']
    responseBody['Data'] = responseData
    json_responseBody = json.dumps(responseBody)
    headers = {
        'content-type' : '',
        'content-length' : str(len(json_responseBody))
    }

    try:
        response = requests.put(responseUrl,
                                data=json_responseBody,
                                headers=headers)
    except Exception as e:
        print("send(..) failed executing requests.put(..): " + str(e))

def parse_region_from_stack(stack_name):
    stack = stack_name.replace("arn:aws:cloudformation:","")
    return stack[:stack.find(":")]

# arn:aws:lambda:us-east-1:845909373636:function:private-link-custom-resource
def validate_vars(resource_properties, event, context):
    print(resource_properties)
    mandatory_vars = ['vpcId','serviceName','ServiceToken']
    optional_vars = ['securityGroupIds','routeTableIds','subnets']
    for var in mandatory_vars:
        if var not in resource_properties:
            send(event, context, FAILED,{}, "Missing " + var)
            return False
    if resource_properties['serviceName'] not in VALID_SERVICES:
        send(event, context, FAILED,{}, "Invalid service name")
        return False
    for var in resource_properties:
        if var not in mandatory_vars and var not in optional_vars:
            send(event, context, FAILED,{}, "Invalid variable " + var)
            return False
    return True

def create(vars,region):
    subnets = []
    security_group_ids = []
    route_table_ids = []
    if 'subnets' in vars:
        subnets=vars['subnets']
    if 'securityGroupIds' in vars:
        security_group_ids=vars['securityGroupIds']
    if 'routeTableIds' in vars:
        route_table_ids=vars['routeTableIds'] 
    service_name = "com.amazonaws." + region + "." + vars['serviceName']
    try:
        response = EC2.create_vpc_endpoint(
            #DryRun=True|False,
            VpcEndpointType='Interface',
            VpcId=vars['vpcId'],
            ServiceName= service_name,
            # PolicyDocument='string',
            RouteTableIds=route_table_ids,
            SubnetIds=subnets,
            SecurityGroupIds=security_group_ids,
            PrivateDnsEnabled=True
        )
        return True
    except:
        return False

def delete(stack_name, resource_id):
    response = CFN.describe_stack_resource(StackName=stack_name,LogicalResourceId=resource_id)
    print(response)

def update(event, context):
    response = CFN.describe_stack_resource(StackName=stack_name,LogicalResourceId=resource_id)
    print(response)

def lambda_handler(event, context):
    if event['RequestType'] == 'Create':
        if validate_vars(event['ResourceProperties'],event,context):
            if create(event['ResourceProperties'], parse_region_from_stack(event['StackId'])):
                send(event, context, SUCCESS,{})
            else:
                send(event, context, FAILED,{})
    elif event['RequestType'] == 'Delete':
        delete(event['StackId'], event['LogicalResourceId'])
        send(event, context, SUCCESS,{})
    else:        
        update(event, context)
        send(event, context, SUCCESS,{})
    return  