class Staking:
    def __init__(self):
        pass

    def stake(self):
        raise NotImplementedError("stake() not implemented")

    def unstake(self):
        raise NotImplementedError("unstake() not implemented")

    def get_rewards(self):
        raise NotImplementedError("get_rewards() not implemented")

    def get_staked_balance(self):
        raise NotImplementedError("get_staked_balance() not implemented")
