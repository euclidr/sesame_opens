import logging
import boto3
from datetime import datetime


def _log_error(message):
    logging.getLogger(__name__).error(message)


def change_a_record_set(zone_id, domain, value,
                        ttl=120, retry=True, comment=None):
    '''change domain's A type record set
    Params:
        zone_id is ID of the hosted zone
        domain is full domain endswith dot
        value is the IP address should be set
        ttl is the resource record cache to live
        retry controls if it should try again if the request is failed
        comment is a comment to the record set, it set to be current time if it is not provided

    Returns if the operation is success
    '''
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
        _log_error('change record set error: {}'.format(e))
        if retry:
            change_a_record_set(zone_id, domain, value,
                                retry=False, comment=comment)
        else:
            return False

    return True
