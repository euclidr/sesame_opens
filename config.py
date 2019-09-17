try:
    from local_settings import * # noqa
except ImportError as e:
    print('Import from local_settings failed, %s' % e)
