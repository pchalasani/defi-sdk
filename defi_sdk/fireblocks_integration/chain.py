from enum import Enum


class Chain(Enum):
    MAINNET = "mainnet"
    ROPSTEN = "ropsten"
    KOVAN = "kovan"
    GOERLI = "goerli"
    RINKEBY = "rinkeby"
    BSC = "bsc"
    BSC_TEST = "bsc_test"
    POLYGON = "polygon"
    POLYGON_TEST = "polygon_mumbai"
    AVALANCHE = "avalanche"
    AVALANCHE_TEST = "avalanche_fuji"
    MOONRIVER = "moonriver"  # Moonbeam testnet
    MOONBEAM = "moonbeam"
    SONGBIRD = "songbird"
    ARBITRUM = "arbitrum"
    ARBITRUM_RIN = "arbitrum_rin"
    FANTOM = "fantom"
    RSK = "rsk_smart_bitcoin"
    RSK_TEST = "rsk smart bitcoin testnet"
    CELO = "celo"
    CELO_BAK = "celo_baklava"
    OPTIMISM = "optimistic_ethereum"
    OPTIMISM_KOVAN = "optimistic ethereum kovan"
    RONIN = "ronin"
    RONIN_TEST = "ronin_test"


CHAIN_TO_ASSET_ID = {
    Chain.MAINNET: ("ETH", "https://cloudflare-eth.com"),
    Chain.ROPSTEN: (
        "ETH_TEST",
        "https://ropsten.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
    ),
    Chain.KOVAN: (
        "ETH_TEST2",
        "https://kovan.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
    ),
    Chain.GOERLI: (
        "ETH_TEST3",
        "https://goerli.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
    ),
    Chain.RINKEBY: (
        "ETH_TEST4",
        "https://rinkeby.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
    ),
    Chain.BSC: ("BNB_BSC", "https://bsc-dataseed.binance.org"),
    Chain.BSC_TEST: ("BNB_TEST", "https://data-seed-prebsc-1-s1.binance.org:8545"),
    Chain.POLYGON: ("MATIC_POLYGON", "https://polygon-rpc.com"),
    Chain.POLYGON_TEST: ("MATIC_POLYGON_MUMBAI", "https://rpc-mumbai.maticvigil.com"),
    Chain.AVALANCHE: ("AVAX", "https://api.avax.network/ext/bc/C/rpc"),
    Chain.AVALANCHE_TEST: ("AVAXTEST", "https://api.avax-test.network/ext/bc/C/rpc"),
    Chain.MOONRIVER: ("MOVR_MOVR", "https://rpc.moonriver.moonbeam.network"),
    Chain.MOONBEAM: ("GLMR_GLMR", "https://rpc.api.moonbeam.network"),
    Chain.SONGBIRD: ("SGB", "https://songbird.towolabs.com/rpc"),
    Chain.ARBITRUM: ("ETH-AETH", "https://rpc.ankr.com/arbitrum"),
    Chain.ARBITRUM_RIN: ("ETH-AETH-RIN", "https://rinkeby.arbitrum.io/rpc"),
    Chain.FANTOM: ("FTM_FANTOM", "https://rpc.ftm.tools/"),
    Chain.RSK: ("RBTC", "https://public-node.rsk.co"),
    Chain.RSK_TEST: ("RBTC_TEST", "https://public-node.testnet.rsk.co"),
    Chain.CELO: ("CELO", "https://rpc.ankr.com/celo"),
    Chain.CELO_BAK: (
        "CELO_BAK",
        "https://baklava-blockscout.celo-testnet.org/api/eth-rpc",
    ),
    Chain.OPTIMISM: ("ETH-OPT", "https://rpc.ankr.com/optimism"),
    Chain.OPTIMISM_KOVAN: (
        "ETH-OPT_KOV",
        "https://optimism-kovan.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
    ),
    Chain.RONIN: ("RON", "https://api.roninchain.com/rpc"),
}
