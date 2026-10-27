
 // SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract PharmaTrace {
    struct Batch {
        string medicineName;
        string batchNumber;
        string manufacturer;
        string expiryDate;
        bool exists;
    }

    struct TraceEvent {
        string status;
        string location;
        uint256 timestamp;
        address recordedBy;
        bytes32 previousHash;
        bytes32 eventHash;
    }

    address public owner;

    mapping(uint256 => Batch) private batches;
    mapping(uint256 => TraceEvent[]) private history;

    event BatchRegistered(
        uint256 indexed batchId,
        string batchNumber,
        address indexed manufacturerAddress
    );

    event TraceRecorded(
        uint256 indexed batchId,
        string status,
        string location,
        uint256 timestamp,
        address indexed recordedBy,
        bytes32 eventHash
    );

    constructor() {
        owner = msg.sender;
    }

    function registerBatch(
        uint256 batchId,
        string calldata medicineName,
        string calldata batchNumber,
        string calldata manufacturer,
        string calldata expiryDate
    ) external {
        require(msg.sender == owner, "Only owner can register");
        require(!batches[batchId].exists, "Batch already registered");

        batches[batchId] = Batch(
            medicineName,
            batchNumber,
            manufacturer,
            expiryDate,
            true
        );

        emit BatchRegistered(batchId, batchNumber, msg.sender);
    }

    function recordEvent(
        uint256 batchId,
        string calldata status,
        string calldata location
    ) external {
        require(batches[batchId].exists, "Unknown batch");

        uint256 count = history[batchId].length;
        bytes32 previousHash = count == 0
            ? bytes32(0)
            : history[batchId][count - 1].eventHash;

        uint256 timestamp = block.timestamp;

        bytes32 eventHash = keccak256(
            abi.encode(
                batchId,
                status,
                location,
                timestamp,
                msg.sender,
                previousHash
            )
        );

        history[batchId].push(
            TraceEvent(
                status,
                location,
                timestamp,
                msg.sender,
                previousHash,
                eventHash
            )
        );

        emit TraceRecorded(
            batchId,
            status,
            location,
            timestamp,
            msg.sender,
            eventHash
        );
    }

    function getBatch(uint256 batchId)
        external
        view
        returns (
            string memory medicineName,
            string memory batchNumber,
            string memory manufacturer,
            string memory expiryDate,
            bool exists
        )
    {
        Batch storage b = batches[batchId];

        return (
            b.medicineName,
            b.batchNumber,
            b.manufacturer,
            b.expiryDate,
            b.exists
        );
    }

    function getEventCount(uint256 batchId)
        external
        view
        returns (uint256)
    {
        return history[batchId].length;
    }

    function getEvent(uint256 batchId, uint256 index)
        external
        view
        returns (
            string memory status,
            string memory location,
            uint256 timestamp,
            address recordedBy,
            bytes32 previousHash,
            bytes32 eventHash
        )
    {
        require(index < history[batchId].length, "Invalid event index");

        TraceEvent storage e = history[batchId][index];

        return (
            e.status,
            e.location,
            e.timestamp,
            e.recordedBy,
            e.previousHash,
            e.eventHash
        );
    }
}
