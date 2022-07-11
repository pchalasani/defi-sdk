# defi-sdk

DeFi SDK is meant to handle ALL interactions with blockchain. It is structured to contain a module for each integrated protocol and a module for utilities needed accross different modules. As a principle, when creating an integration with a protocol, only functionalities that are needed at this time should be done. If only tracking data is needed, no transaction integrations are needed for example.

## Current integrations
- Aave v2
    - Data gathering
- Aave v3
    - Data gathering
    - Transactions
- Uniswap v2
    - Data gathering
    - Transactions
- Staking (generalized frame for getting staked amount + accumulated rewards)
    - Quickswap LP staking