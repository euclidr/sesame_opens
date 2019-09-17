import boto3
from datetime import datetime


def change_a_record_set(zone_id, domain, value,
                        ttl=120, retry=True, comment=None):
    if comment is None:
        comment = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    change_batch = {
        'Comment': comment,
        'Changes': [{
            'Action': 'UPSERT',
            'ResourceRecordSet': {
                'Name': domain,
                'Type': 'A',
                'TTL': 120,
                'ResourceRecords': [{'Value': value}]
            }
        }]
    }
    cli = boto3.client('route53')
    try:
        cli.change_resource_record_sets(HostedZoneId=zone_id,
                                        ChangeBatch=change_batch)
    except Exception as e:
        print('change record set error: {}'.format(e))
        if retry:
            change_a_record_set(zone_id, domain, value,
                                retry=False, comment=comment)
        else:
            return False

    return True



# ChangeBatch = {
#     'Comment': '2019-09-17',
#     'Changes': [{
#         'Action': 'UPSERT',
#         'ResourceRecordSet': {
#             'Name': 'b.surfscientifically.com.',
#             'Type': 'A',
#             'TTL': 120,
#             'ResourceRecords': [{
#                 'Value': '5.6.7.8'
#             }]
#         }
#     }]
# }
