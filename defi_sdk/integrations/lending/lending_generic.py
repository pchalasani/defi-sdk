class Lending:
    def __init__(self):
        pass

    def borrow(self):
        raise NotImplementedError("borrow not implemented")

    def repay(self):
        raise NotImplementedError("repay not implemented")

    def add_collateral(self):
        raise NotImplementedError("add_collateral() not implemented")

    def withdraw_collateral(self):
        raise NotImplementedError("withdraw_collateral() not implemented")
