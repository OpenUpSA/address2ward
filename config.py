import logging
import logging.config
import os

FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgres://wards:wards@127.0.0.1:5432/wards')

DEBUG = FLASK_ENV == 'production'

DATABASES = (
    'vd_2014',
    'police',
    'wards_2006',
    'wards_2011',
    'census_2011',
    )

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(process)-6d %(name)-12s %(levelname)-8s %(message)s',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG'
    },
    'loggers': {
        'address2ward': {
            'level': 'DEBUG',
        },
    }
})

logger = logging.getLogger('address2ward')
