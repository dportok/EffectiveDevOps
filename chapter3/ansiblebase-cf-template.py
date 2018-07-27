"""Generating CloudFormation template."""
from ipaddress import ip_network
from ipify import get_ip
from troposphere import (
    Base64,
    ec2,
    GetAtt,
    Join,
    Output,
    Parameter,
    Ref,
    Template,
)
ApplicationName = "helloworld"
ApplicationPort = "3000"
PublicCidrIp = str(ip_network(get_ip()))
GithubAccount = "dportok"
GithubAnsibleURL = "https://github.com/{}/EffectiveDevOps.git".format(GithubAccount)
AnsiblePullCmd = "/usr/local/bin/ansible-pull -U {} {}.yaml -i localhost".format(GithubAnsibleURL,ApplicationName)
t = Template()

t.add_description("Effective DevOps in AWS: HelloWorld web application")

t.add_parameter(Parameter(
    "awstest",
    Description="Name of an existing EC2 KeyPair to SSH",
    Type="AWS::EC2::KeyPair::KeyName",
    ConstraintDescription="must be the name of an existing EC2 KeyPair.",
))

t.add_resource(ec2.SecurityGroup(
    "SecurityGroup",
    GroupDescription="Allow SSH and TCP/{} access".format(ApplicationPort),
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort="22",
            ToPort="22",
            CidrIp=PublicCidrIp,
        ),
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort=ApplicationPort,
            ToPort=ApplicationPort,
            CidrIp="0.0.0.0/0",
        ),
    ],
))

ud = Base64(Join('\n', [
    "#!/bin/bash",
    "sudo yum install --enablerepo=epel -y git",
    "sudo yum -y install python34",
    "sudo wget https://bootstrap.pypa.io/get-pip.py -O /home/ec2-user/get-pip.py",
    "sudo python3 /home/ec2-user/get-pip.py --user",
    "sudo pip install --upgrade pip",
    "sudo /usr/local/bin/pip install --upgrade setuptools",
    "sudo /usr/local/bin/pip install ansible",
    AnsiblePullCmd,
    "sudo echo '*/10 * * * * ec2-user {}' > /etc/cron.d/ansible-pull".format(AnsiblePullCmd)
]))

t.add_resource(ec2.Instance(
    "instance",
    ImageId="ami-a4c7edb2",
    InstanceType="t2.micro",
    SecurityGroups=[Ref("SecurityGroup")],
    KeyName=Ref("awstest"),
    UserData=ud,
))

t.add_output(Output(
    "InstancePublicIp",
    Description="Public IP of our instance.",
    Value=GetAtt("instance", "PublicIp"),
))

t.add_output(Output(
    "WebUrl",
    Description="Application endpoint",
    Value=Join("", [
        "http://", GetAtt("instance", "PublicDnsName"),
        ":", ApplicationPort
    ]),
))

print(t.to_json())