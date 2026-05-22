import uuid

class Item:
    def __init__(self, block_uid=None, description=None):
        self.unique_id = uuid.uuid4()
        self.block_uid = block_uid
        self.description = description

    def get_block(self, map_instance):
        return map_instance.get_block_by_uid(self.block_uid)