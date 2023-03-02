from pyteal import *


def approval_program():

    on_creation = Seq([
        App.globalPut(Bytes("random number"), Int(1111)),
        Approve()
    ])

    get_randomness = Seq(
        # Prep arguments
        (round_number := abi.Uint64()).set(Btoi(Txn.application_args[1])),
        (user_data := abi.make(abi.DynamicArray[abi.Byte])).set([]),
        InnerTxnBuilder.ExecuteMethodCall(
            app_id=Txn.applications[1],
            method_signature="must_get(uint64,byte[])byte[]",
            args=[round_number, user_data],
        ),
        # Remove first 4 bytes (ABI return prefix)
        # and return the rest
        Suffix(InnerTxn.last_log(), Int(33))
    )

    vrf = Seq(
        # # Get the randomness back
        (randomness_number := abi.DynamicBytes()).decode(get_randomness),
        App.globalPut(Bytes('random number'), Btoi(randomness_number.get())),
        Approve()
    )

    call_transaction = Cond(
        [Txn.application_args[0] == Bytes("random"), vrf]
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.NoOp, call_transaction]
    )

    return program


def clearstate_contract():
    return Approve()


if __name__ == "__main__":
    with open("smart_contract.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=7)
        f.write(compiled)