
const fs = require("fs");
const path = require("path");
const solc = require("solc");

const contractPath = path.join(
  __dirname,
  "contracts",
  "PharmaTrace.sol"
);

const source = fs.readFileSync(contractPath, "utf8");

const input = {
  language: "Solidity",
  sources: {
    "PharmaTrace.sol": { content: source }
  },
  settings: {
    optimizer: {enabled: true, runs: 200},
    evmVersion: "paris",
    outputSelection: {"*": {"*": ["abi", "evm.bytecode.object"]}}
}
};

const output = JSON.parse(
  solc.compile(JSON.stringify(input))
);

if (output.errors) {
  for (const error of output.errors) {
    console.log(error.formattedMessage);
  }

  if (output.errors.some(e => e.severity === "error")) {
    process.exit(1);
  }
}

const contract = output.contracts["PharmaTrace.sol"]["PharmaTrace"];

const artifact = {
  abi: contract.abi,
  bytecode: "0x" + contract.evm.bytecode.object
};

const outDir = path.join(__dirname, "artifacts");
fs.mkdirSync(outDir, { recursive: true });

fs.writeFileSync(
  path.join(outDir, "PharmaTrace.json"),
  JSON.stringify(artifact, null, 2)
);

console.log("Contract compiled successfully!");
console.log("Artifact: artifacts/PharmaTrace.json");
