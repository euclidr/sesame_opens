
import logging
import boto3
from datetime import datetime


def _log_error(message):
    logging.getLogger(__name__).error(message)


def _get_attached_ip_name(cli, instance_name, page_token=''):
    '''get attached static ip name of the instance
    there are no ways to get it directly, we must iterate all
    static ips and check if it is attached to that instance.

    raise Exception if the static ip not found.
    '''
    batch = cli.get_static_ips(pageToken=page_token)
    next_token = batch.get('nextPageToken', '')
    for info in batch['staticIps']:
        if info.get('attachedTo', '') == instance_name:
            return info['name']

    if next_token:
        return _get_attached_ip_name(cli, instance_name, page_token=next_token)
    else:
        raise Exception('cant find static ip attach to {}'
                        .format(instance_name))


def _detach_static_ip(cli, instance_name):
    '''detach static ip of the instance

    raise Exception if static ip not found or detach failed.
    '''
    ip_name = _get_attached_ip_name(cli, instance_name)
    result = cli.detach_static_ip(staticIpName=ip_name)
    if not result['operations']:
        raise Exception('invalid detach result: instance: {}, ip_name: {}'
                        .format(instance_name, ip_name))
    if result['operations'][0]['status'] != 'Succeeded':
        raise Exception('detach failed: instance: {}, ip_name: {}, error: {}'
                        .format(
                            instance_name,
                            ip_name,
                            result['operations'][0]['errorDetails']),)


def _allocate_static_ip(cli, name_prefix):
    '''allocate a static ip with name combined with name_prefix and time

    raise Exception when the operation failed. The number of unattached
    static ip that can be allocated is limited.
    '''
    ip_name = name_prefix + datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    result = cli.allocate_static_ip(staticIpName=ip_name)
    if not result['operations']:
        raise Exception('invalid allocate static ip result')
    if result['operations'][0]['status'] != 'Succeeded':
        raise Exception('allocate static ip failed, error: {}',
                        result['operations']['errorDetails'])

    return ip_name


def _attach_static_ip(cli, ip_name, instance_name):
    '''attach static ip to the instance

    raise Exception when the operation failed
    '''
    result = cli.attach_static_ip(staticIpName=ip_name,
                                  instanceName=instance_name)
    if not result['operations']:
        raise Exception('invalid attach static ip result')
    if result['operations'][0]['status'] != 'Succeeded':
        raise Exception('attach static ip failed, error: {}',
                        result['operations']['errorDetails'])


def _release_static_ip(cli, ip_name):
    '''release the static ip'''
    try:
        cli.release_static_ip(staticIpName=ip_name)
    except Exception as e:
        _log_error('release static ip {} error: {}'.format(
            ip_name, e
        ))


def _release_unused_static_ips(cli, prefix, page_token=''):
    '''iterate all static ips and release the unattached ones
    with the prefix
    '''
    try:
        batch = cli.get_static_ips(pageToken=page_token)
        next_token = batch.get('nextPageToken', '')
        for ip_info in batch['staticIps']:
            if not ip_info['isAttached']\
               and ip_info['name'].startswith(prefix):
                _release_static_ip(cli, ip_info['name'])

    except Exception as e:
        _log_error('release unused static ips error: {}'.format(e))
        return

    if next_token:
        _release_unused_static_ips(cli, prefix, page_token=page_token)


def _get_instance_ip(cli, instance_name):
    '''get the instanc's public ip'''
    try:
        instance = cli.get_instance(instanceName=instance_name)
        return instance['instance']['publicIpAddress']
    except Exception as e:
        _log_error('get instance ip error: {}'.format(e))


def change_public_ip(instance_name, ip_name_prefix):
    '''change the instance's public IP
    allocate a new static IP then attach to the instance.

    Return if IP is changed and the new and old IPs
    '''

    cli = boto3.client('lightsail')

    old = _get_instance_ip(cli, instance_name)
    if not old:
        _log_error('can not get instance {} public IP'.format(instance_name))
        return False, '', ''

    try:
        instance = cli.get_instance(instanceName=instance_name)
        if instance['instance']['isStaticIp']:
            _detach_static_ip(cli, instance_name)
        ip_name = _allocate_static_ip(cli, ip_name_prefix)
        _attach_static_ip(cli, ip_name, instance_name)
    except Exception as e:
        _log_error('change public ip error: {}'.format(e))
    finally:
        _release_unused_static_ips(cli, ip_name_prefix)
        new = _get_instance_ip(cli, instance_name)
        if not new:
            _log_error('can not get instance {} new public IP'
                       .format(instance_name))
            return False, '', ''

        return new != old, new, old


if __name__ == '__main__':
    InstanceName = 'test-1'
    IpNamePrefix = 'test_ip_'
    _log_error(change_public_ip(InstanceName, IpNamePrefix))
