DEBUG = True
SECRET_KEY = 'some_secret'

SESAME_OPENS = 'xxxx'

HOSTED_ZONE_ID = 'xxxxxxxx'
RECORD_SET_NAME = 'some.domain'

INSTANCE_NAME = 'Ubuntu-Tokyo-1'
IP_NAME_PREFIX = 'open_the_wall_'

RECORD_BASE_PATH = ''

try:
    from local_settings import * # noqa
except ImportError as e:
    print('Import from local_settings failed, %s' % e)
