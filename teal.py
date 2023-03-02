from algosdk import encoding
from pyteal import *
from algosdk.v2client import algod


def client():
    algod_address = "https://testnet-algorand.api.purestake.io/ps2"
    algod_token = "K7DgVll3W19DdHA3FTduX4XZTuCvTFf32HXUP5E4"
    headers = {"X-API-Key": algod_token}
    conn = algod.AlgodClient(algod_token, algod_address, headers)

    return conn


# define the algod client
algod_client = client()


# convert pyteal to teal (application)
def to_teal(smart_contract):

    # First convert the PyTeal to TEAL
    teal_campaign = compileTeal(smart_contract, Mode.Application, version=6)

    # Next compile our TEAL to bytecode. (it's returned in base64)
    b64_campaign = algod_client.compile(teal_campaign)['result']

    # Lastly decode the base64.
    prog_campaign = encoding.base64.b64decode(b64_campaign)

    return prog_campaign

