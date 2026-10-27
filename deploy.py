
import json
from pathlib import Path
from web3 import Web3

ROOT = Path(__file__).resolve().parent
RPC_URL = "http://127.0.0.1:8545"
ARTIFACT = ROOT / "artifacts" / "PharmaTrace.json"
OUTPUT = ROOT / "deployment.json"

w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    raise SystemExit(
        "Cannot connect to Ganache. Start Ganache on port 8545 first."
    )

artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
account = w3.eth.accounts[0]

factory = w3.eth.contract(
    abi=artifact["abi"],
    bytecode=artifact["bytecode"]
)

tx_hash = factory.constructor().transact({"from": account})
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

if receipt.status != 1 or not receipt.contractAddress:
    raise SystemExit("Contract deployment failed.")

deployment = {
    "address": receipt.contractAddress,
    "abi": artifact["abi"],
    "deployer": account,
    "deployment_tx": tx_hash.hex(),
    "block_number": receipt.blockNumber,
    "chain_id": w3.eth.chain_id
}

OUTPUT.write_text(
    json.dumps(deployment, indent=2),
    encoding="utf-8"
)

print("Contract deployed successfully!")
print("Network chain ID:", w3.eth.chain_id)
print("Contract address:", receipt.contractAddress)
print("Deployment transaction:", tx_hash.hex())
print("Saved deployment.json")
