# sesame_opens

Change Lightsail's public IP using boto3 APIs.

### How to use

1. deploy a lightsail instance somewhere with a name `<instance_name>`
2. host domain zone in Route53 and get `<hosted_zone_id>`
3. create an IAM account with Route53 fullaccess and lightsail privileges:
    ```
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "lightsail:GetInstances",
                    "lightsail:GetStaticIps",
                    "lightsail:AttachStaticIp",
                    "lightsail:GetStaticIp",
                    "lightsail:ReleaseStaticIp",
                    "lightsail:GetInstance",
                    "lightsail:DetachStaticIp",
                    "lightsail:AllocateStaticIp"
                ],
                "Resource": "*"
            }
        ]
    }
    ```
4. get IAM token and set it with `aws configure` command
5. add `local_settings.py` in project root
    ```
    SECRET_KEY = 'xxx' # secret_key used by flask
    SESAME_OPENS = 'xxx' # the secret code inputed before pressing Sesame Opens button

    HOSTED_ZONE_ID = <hosted_zone_id>
    RECORD_SET_NAME = <full_domain_name>

    INSTANCE_NAME = <instance_name>
    IP_NAME_PREFIX = <ip_name_prefix> # prefix that identify static ips allocated by the project.
    ```
6. `python app.py` or run from gunicorn

### License

MIT