import boto3


LEVEL_MAP = [
    'DEBUG',
    'INFO',
    'ERROR',
    'CRITICAL',
]

class WatchTowerLogger:
    default_handler = 'watchtower.CloudWatchLogHandler'
    use_queues = False


    def __init__(self, modules, env, boto3_session, custom_handler='watchtower'):
        self.boto3_session = boto3_session
        self.modules = modules
        self.handlers_dict = {}
        self.loggers_dict = {}
        self.environment_name = env
        self.custom_logger_handler = custom_handler
        self.setup()

    def setup_boto3(self):
        self.boto3_session = boto3.session.Session()

    def create_handler(self, module, level):
        handler = {}
        handler_name = "{}_{}_{}".format(self.custom_logger_handler, module, level.lower())
        handler[handler_name] = {
                    'level' : level.upper(),
                    'class' : self.default_handler,
                    'boto3_session' : self.boto3_session,
                    'log_group' : "{}-{}".format(
                        self.environment_name, module),
                    'stream_name' : level.lower(),
                    'use_queues' : self.use_queues,
                    'formatter' : 'aws'
        }
        self.update_attrs(module, handler_name)
        return handler

    def update_attrs(self, module, handler_name):
        if not module in self.__dict__:
            self.__dict__[module] = [handler_name]
        else:
            self.__dict__[module].append(handler_name)

    def create_logger(self, module, levels, propagate):
        """
         Adds the less important level as initial level for logger.
        """
        int_levels = list(map(lambda level: LEVEL_MAP.index(level), levels))
        sorted_int_levels = sorted(int_levels)
        logger_data = {
           'handlers' : getattr(self, module),
           'level' : LEVEL_MAP[sorted_int_levels[0]],
           'propagate': propagate
        }
        if not propagate:
            logger_data.pop('propagate')
        self.loggers_dict[module] = logger_data

    def setup(self):
        for module, data_dict in self.modules.items():
            levels = data_dict['levels']
            generate_handler = data_dict.get('generate_logger', True)
            propagate = data_dict.get('propagate', False)
            module_handlers = [self.create_handler(module, level) for level in levels]
            for handler in module_handlers:
                self.handlers_dict.update(handler)
            if generate_handler:
                self.create_logger(module, levels, propagate)
            #map(lambda x: setattr(self, module, x), [handler['name'] for handler in module_handlers])

    def get_handlers(self):
        return self.handlers_dict

    def get_loggers(self):
        return self.loggers_dict
