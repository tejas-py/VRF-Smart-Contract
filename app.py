from algosdk.future import transaction
from algosdk import account, mnemonic
from algosdk.v2client import algod

def algo_client():
    algod_address = "https://testnet-algorand.api.purestake.io/ps2"
    algod_token = "K7DgVll3W19DdHA3FTduX4XZTuCvTFf32HXUP5E4"
    headers = {"X-API-Key": algod_token}
    conn = algod.AlgodClient(algod_token, algod_address, headers)

    return conn


def compile_program(client, source_code):
    compile_response = client.compile(source_code.decode('utf-8'))
    return base64.b64decode(compile_response['result'])


def wait_for_confirmation(client, txid):
    last_round = client.status().get('last-round')
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        print("Waiting for confirmation...")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
        print("Transaction {} confirmed in round {}.".format(txid, txinfo.get('confirmed-round')))
        return txinfo


# Declare application state storage (immutable)
local_ints = 0
local_bytes = 0
global_ints = 1
global_bytes = 1
global_schema = transaction.StateSchema(global_ints, global_bytes)
local_schema = transaction.StateSchema(local_ints, local_bytes)

approval_program_source = b"""#pragma version 7
txn ApplicationID
int 0
==
bnz main_l6
txn OnCompletion
int NoOp
==
bnz main_l3
err
main_l3:
txna ApplicationArgs 0
byte "random"
==
bnz main_l5
err
main_l5:
int 27952900
store 0
int 0
store 2
load 2
itob
extract 6 0
byte ""
concat
store 1
itxn_begin
int appl
itxn_field TypeEnum
txna Applications 1
itxn_field ApplicationID
method "must_get(uint64,byte[])byte[]"
itxn_field ApplicationArgs
load 0
itob
itxn_field ApplicationArgs
load 1
itxn_field ApplicationArgs
itxn_submit
itxn LastLog
extract 4 0
store 3
byte "random number"
load 3
extract 2 0
int 0
getbit
app_global_put
int 1
return
main_l6:
byte "random number"
int 1111
app_global_put
int 1
return
"""

clear_program_source = b"""#pragma version 7
int 1
"""


def create_app(account_mnemonic):
    client = algo_client()
    # import smart contract for the application
    approval_program = compile_program(client, approval_program_source)
    clear_program = compile_program(client, clear_program_source)

    private_key = mnemonic.to_private_key(account_mnemonic)
    sender = account.address_from_private_key(private_key)

    on_complete = transaction.OnComplete.NoOpOC.real

    params = client.suggested_params()

    txn = transaction.ApplicationCreateTxn(sender, params, on_complete,
                                           approval_program, clear_program,
                                           global_schema, local_schema)

    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()
    client.send_transactions([signed_txn])
    wait_for_confirmation(client, tx_id)
    transaction_response = client.pending_transaction_info(tx_id)
    app_id = transaction_response['application-index']
    print(f"Created Application: {app_id}")

    return app_id


def call_app(app_id, account_mnemonic):

    client = algo_client()

    params = client.suggested_params()
    params.fee = 2000

    app_args = ['random']
    private_key = mnemonic.to_private_key(account_mnemonic)
    sender = account.address_from_private_key(private_key)

    txn = transaction.ApplicationNoOpTxn(sender, params, app_id, app_args, foreign_apps=[110096026])

    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()
    client.send_transactions([signed_txn])
    wait_for_confirmation(client, tx_id)

    return txn


if __name__ == "__main__":

    account1 = "sunset year win conduct length lens census tissue town coyote member speak peanut client magnet orbit law there bid excuse frame hill air absorb country"
    account2 = "myth copper sock coach hurt hammer grace similar vacant physical congress milk own actress screen lesson never survey extend blouse drip table shock about honey"

    # created_application = create_app(account1)
    tx_id = call_app(160599095, account2)
