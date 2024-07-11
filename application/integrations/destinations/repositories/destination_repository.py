from common.redis.redis_config import redis_client
from common.destinations.base_destination import BaseDestination
import pickle

class DestinationRepository:
    @staticmethod
    def store_config_in_redis(integration_type: str, config: dict):
        redis_client.hmset(integration_type, config)

    @staticmethod
    def store_creator_in_redis(integration_type: str, creator):
        serialized_creator = pickle.dumps(creator)
        redis_client.set(f"{integration_type}_creator", serialized_creator)

    @classmethod
    def register_integration(cls, integration_type: str, config: dict = None, creator = None):
        if config:
            cls.store_config_in_redis(integration_type, config)
        if creator:
            cls.store_creator_in_redis(integration_type, creator)

    @classmethod
    def create_integration(cls, integration_type: str) -> BaseDestination:
        creator = cls._retrieve_creator_from_redis(integration_type)
        if not creator:
            raise ValueError(f"Unsupported integration type: {integration_type}")
        
        config = cls._retrieve_config_from_redis(integration_type)
        if not config:
            raise ValueError(f"No configuration found for integration type: {integration_type}")
        
        return creator(**config)

    @staticmethod
    def _retrieve_config_from_redis(integration_type: str):
        config = redis_client.hgetall(integration_type + "_destination")
        if not config:
            return None
        return {k.decode('utf-8'): v.decode('utf-8') for k, v in config.items()}

    @staticmethod
    def _retrieve_creator_from_redis(integration_type: str):
        serialized_creator = redis_client.get(f"{integration_type}_destination_creator")
        if not serialized_creator:
            return None
        return pickle.loads(serialized_creator)

    @classmethod
    def get_integration(cls, integration_type: str) -> BaseDestination:
        creator = cls._retrieve_creator_from_redis(integration_type)
        if not creator:
            raise ValueError(f"Unsupported integration type: {integration_type}")
        
        config = cls._retrieve_config_from_redis(integration_type)
        if not config:
            raise ValueError(f"No configuration found for integration type: {integration_type}")
        
        integration = creator(**config)
        integration.connect()
        return integration