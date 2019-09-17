
import boto3
from datetime import datetime


def _get_attached_ip_name(cli, instance_name, page_token=''):
    batch = cli.get_static_ips(pageToken=page_token)
    next_token = batch.get('nextPageToken', '')
    for ip_info in batch['staticIps']:
        if ip_info.get('attachedTo', '') == instance_name:
            return ip_info['name']

    if next_token:
        return _get_attached_ip_name(cli, instance_name, page_token=next_token)
    else:
        raise Exception("cant find static ip attach to {}"
                        .format(instance_name))


def _detach_static_ip(cli, instance_name):
    ip_name = _get_attached_ip_name(cli, instance_name)
    result = cli.detach_static_ip(staticIpName=ip_name)
    if not result['operations']:
        raise Exception("invalid detach result: instance: {}, ip_name: {}"
                        .format(instance_name, ip_name))
    if result['operations'][0]['status'] != 'Succeeded':
        raise Exception("detach failed: instance: {}, ip_name: {}, error: {}"
                        .format(
                            instance_name,
                            ip_name,
                            result['operations'][0]['errorDetails']),)


def _allocate_static_ip(cli, name_prefix):
    ip_name = name_prefix + datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    result = cli.allocate_static_ip(staticIpName=ip_name)
    if not result['operations']:
        raise Exception('invalid allocate static ip result')
    if result['operations'][0]['status'] != 'Succeeded':
        raise Exception("allocate static ip failed, error: {}",
                        result['operations']['errorDetails'])

    return ip_name


def _attach_static_ip(cli, ip_name, instance_name):
    result = cli.attach_static_ip(staticIpName=ip_name,
                                  instanceName=instance_name)
    if not result['operations']:
        raise Exception('invalid attach static ip result')
    if result['operations'][0]['status'] != 'Succeeded':
        raise Exception("attach static ip failed, error: {}",
                        result['operations']['errorDetails'])


def _release_unused_static_ip(cli, ip_name):
    try:
        cli.release_static_ip(staticIpName=ip_name)
    except Exception as e:
        print('release static ip {} error: {}'.format(
            ip_name, e
        ))


def _release_unused_static_ips(cli, ip_name_prefix, page_token=''):
    try:
        batch = cli.get_static_ips(pageToken=page_token)
        next_token = batch.get('nextPageToken', '')
        for ip_info in batch['staticIps']:
            if not ip_info['isAttached']\
               and ip_info['name'].startswith(ip_name_prefix):
                _release_unused_static_ip(cli, ip_info['name'])

    except Exception as e:
        print("release unused static ips error: {}".format(e))
        return

    if next_token:
        _release_unused_static_ips(cli, ip_name_prefix, page_token=page_token)


def _get_instance_ip(cli, instance_name):
    try:
        instance = cli.get_instance(instanceName=instance_name)
        return instance['instance']['publicIpAddress']
    except Exception as e:
        print('get instance ip error: {}'.format(e))


def change_public_ip(instance_name, ip_name_prefix):
    cli = boto3.client('lightsail')
    old_ip = _get_instance_ip(cli, instance_name)
    if not old_ip:
        print("can't get instance {} public IP".format(instance_name))
        return False, '', ''

    try:
        instance = cli.get_instance(instanceName=instance_name)
        if instance['instance']['isStaticIp']:
            _detach_static_ip(cli, instance_name)
        ip_name = _allocate_static_ip(cli, ip_name_prefix)
        _attach_static_ip(cli, ip_name, instance_name)
    except Exception as e:
        print(e)
    finally:
        _release_unused_static_ips(cli, ip_name_prefix)
        new_ip = _get_instance_ip(cli, instance_name)
        if not new_ip:
            print("can't get instance {} new public IP".format(instance_name))
            return False, '', ''

        return new_ip != old_ip, new_ip, old_ip


if __name__ == '__main__':
    InstanceName = 'test-1'
    IpNamePrefix = 'test_ip_'
    print(change_public_ip(InstanceName, IpNamePrefix))
